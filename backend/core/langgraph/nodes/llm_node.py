from typing import Dict, Any, List
import os
import json
import logging
import re
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from ..state import WorkflowState
from ..tools.menu_tools import get_all_menus, get_menu_info, get_menu_options

logger = logging.getLogger("llm_node")

def analyze_order(state: WorkflowState) -> Dict[str, Any]:
    try:
        # API 키 -> env 파일에서 긁어와야함
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY env var 설정 X")
            raise ValueError("OPENAI_API_KEY env var 설정 X")
            
        llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0.0,
            openai_api_key=api_key
        )
        
        text_input = state.get('text', '')
        logger.info(f"LLM 분석 시작: 텍스트='{text_input}'")
        
        # 명확화 항목 해결 여부 플래그 초기화 (항상 이 플래그를 포함하도록)
        state["pending_clarifications_resolved"] = False
        
        all_menus = get_all_menus()
        if all_menus.get("status") != "success":
            logger.warning("전체 메뉴 조회 실패")
            menu_info = "메뉴 정보를 가져오지 못했습니다."
        else:
            menu_info = "메뉴 정보:\n"
            for category in all_menus.get("categories", []):
                menu_info += f"\n## {category.name}\n"
                for item in category.items:
                    menu_info += f"- {item.name}: {item.base_price}원\n"
                    
                    if hasattr(item, 'required_options') and item.required_options:
                        menu_info += "  필수 옵션:\n"
                        for option_category, options in item.required_options.items():
                            menu_info += f"    {option_category}: "
                            option_texts = []
                            for opt in options:
                                price_text = f"({'+' if opt.price_adjustment > 0 else ''}{opt.price_adjustment}원)" if opt.price_adjustment != 0 else ""
                                option_texts.append(f"{opt.name}{price_text}")
                            menu_info += ", ".join(option_texts) + "\n"
                    
                    if hasattr(item, 'optional_options') and item.optional_options:
                        menu_info += "  선택 옵션:\n"
                        for option_category, options in item.optional_options.items():
                            menu_info += f"    {option_category}: "
                            option_texts = []
                            for opt in options:
                                price_text = f"({'+' if opt.price_adjustment > 0 else ''}{opt.price_adjustment}원)" if opt.price_adjustment != 0 else ""
                                option_texts.append(f"{opt.name}{price_text}")
                            menu_info += ", ".join(option_texts) + "\n"
        
        system_prompt = f"""당신은 카페 주문을 돕는 AI 어시스턴트이다.
        사용자의 음성 주문을 분석하고, 주문을 정확하게 처리하기 위해 필요한 정보를 수집해야 한다.
        
        아래 정보를 참고하라:
        {menu_info}
        
        주문 분석 시 다음 사항을 고려하라:
        1. 메뉴 이름과 수량
        2. 필수 옵션 (온도, 크기)
        3. 선택 옵션 (커피는 디카페인 여부, 티는 휘핑크림 추가 여부)
        4. 특별 요청사항
        
        응답은 다음 JSON 형식으로 제공하라:
        {{
            "is_order_related": true or false,
            "greeting_response": "주문과 관련 없는 대화인 경우 여기에 응답을 제공하라",
            "items": [
                {{
                    "name": "메뉴명",
                    "quantity": 수량,
                    "options": ["옵션1", "옵션2"],
                    "missing_required_options": ["필수옵션1", "필수옵션2"],
                    "price": 가격
                }}
            ],
            "total_price": 총 가격,
            "special_requests": "특별 요청사항",
            "clarification_items": ["명확하지 않은 항목1"]
        }}
        
        사용자의 입력이 주문과 관련이 없는 경우(예: 인사, 날씨 질문, 대화 나누기 등):
        1. "is_order_related"를 false로 설정하라.
        2. "greeting_response"에 적절한 대화 응답을 제공하라.
        3. 다른 주문 관련 필드는 빈 배열이나 기본값으로 설정하라.
        4. 기존 주문 상태는 변경하지 마라.
        
        주문 내용이 불완전하거나 명확하지 않은 경우, 다음 규칙에 따라 명확화를 요청하라:
        
        1. 항상 하나의 메뉴 항목당 필수 옵션(온도, 크기)이 모두 지정되었는지 확인하라. 필수 옵션이 누락된 경우, "온도"와 "크기" 옵션에 대해 구체적으로 질문하라.
           - 온도 옵션이 누락된 경우: "<메뉴명>을 따뜻한 음료로 드릴까요, 차가운 음료로 드릴까요?"
           - 크기 옵션이 누락된 경우: "<메뉴명>을 레귤러 사이즈로 드릴까요, 라지 사이즈로 드릴까요?"
           
        2. clarification_items 배열에는 한 번에 하나의 질문만 포함하라. 여러 항목을 물어봐야 한다면 가장 중요한 것 하나만 질문하라.
        
        3. 가격을 직접 묻지 마라. 가격은 메뉴 정보에서 확인할 수 있다.
        
        4. 선택 옵션에 대해서도 물어볼 수 있다. 선택 옵션은 필수는 아니지만, 사용자 경험을 향상시킬 수 있다:
           - 커피 메뉴의 경우: "<메뉴명>을 디카페인으로 드릴까요, 일반 카페인으로 드릴까요?"
           - 티 메뉴의 경우: "<메뉴명>에 휘핑크림을 추가할까요?"
           
        5. 필수 옵션이 모두 선택되었고 더 이상 명확화할 항목이 없을 때, 사용자에게 "더 주문하실 것이 있으신가요?"라고 greeting_response에 추가하고, clarification_items은 빈 배열로 설정하라.
        
        이전 대화와 보류 중인 명확화 항목을 고려하여 응답하라. 이미 응답된 항목에 대해서는 다시 물어보지 마라라.
        """
        
        messages = [SystemMessage(content=system_prompt)]
        
        # 이전 대화 기록 추가
        conversation_history = state.get("conversation_history", [])
        pending_clarifications = state.get("pending_clarifications", [])
        
        # 대화 기록이 있으면 메시지에 추가
        if conversation_history:
            conversation_summary = "이전 대화:\n"
            for conv in conversation_history:
                role = conv.get("role", "")
                content = conv.get("content", "")
                conversation_summary += f"{role}: {content}\n"
            
            messages.append(HumanMessage(content=f"대화 기록: {conversation_summary}"))
        
        # 보류 중인 명확화 항목이 있으면 추가
        if pending_clarifications:
            clarification_summary = "아직 명확하지 않은 항목들:\n"
            for item in pending_clarifications:
                clarification_summary += f"- {item}\n"
            
            messages.append(HumanMessage(content=f"명확화 필요 항목: {clarification_summary}"))
        
        # 현재 주문 상태 추가 (있는 경우만..)
        current_order = state.get("current_order")
        if current_order:
            order_summary = "현재 주문 상태:\n"
            for item in current_order.get("items", []):
                item_name = item.get("name", "")
                quantity = item.get("quantity", 1)
                options = ", ".join(item.get("options", []))
                missing_options = item.get("missing_required_options", [])
                if missing_options:
                    missing_str = f" (누락된 필수 옵션: {', '.join(missing_options)})"
                else:
                    missing_str = ""
                order_summary += f"- {item_name} x {quantity} (옵션: {options}){missing_str}\n"
            
            messages.append(HumanMessage(content=f"현재 주문: {order_summary}"))
        
        # 현재 사용자 입력 추가
        messages.append(HumanMessage(content=f"현재 사용자 입력: {text_input}"))
        
        logger.info("OpenAI API 호출 중...")
        response = llm.invoke(messages)
        logger.info("OpenAI API 응답 수신 완료")
        
        try:
            logger.info(f"LLM 응답 분석 중: {response.content}")
            
            response_content = response.content.strip()
            if response_content.startswith('{') and response_content.endswith('}'):
                analysis = json.loads(response_content)
            else:
                json_match = re.search(r'({.*})', response_content, re.DOTALL)
                if json_match:
                    analysis = json.loads(json_match.group(1))
                else:
                    raise ValueError("LLM 응답에서 JSON 형식을 찾을 수 없습니다.")
            
            is_order_related = analysis.get("is_order_related", True)
            
            # 주문과 관련 없는 대화인 경우,
            if not is_order_related:
                greeting_response = analysis.get("greeting_response", "무엇을 도와드릴까요?")
                logger.info(f"주문과 관련 없는 대화 감지: '{greeting_response}'")
                
                # 대기 중인 clarification 항목이 있는지 확인
                has_pending_clarifications = False
                if "pending_clarifications" in state and state["pending_clarifications"]:
                    has_pending_clarifications = True
                    logger.info(f"기존 클래리피케이션 항목 유지: {state['pending_clarifications']}")
                
                # 현재 상태를 유지하면서 응답만 업데이트
                state["response"] = {
                    "message": greeting_response,  # greeting_response를 메시지로 사용
                    "needs_clarification": has_pending_clarifications,  # 클래리피케이션 상태 유지
                    "clarification_items": state.get("pending_clarifications", []) if has_pending_clarifications else [],
                    "is_casual_conversation": True
                }
                
                # 기존 주문 정보가 있는 경우 유지
                if "analysis" not in state:
                    state["analysis"] = {
                        "items": [],
                        "total_price": 0,
                        "special_requests": "",
                        "clarification_items": []
                    }
                elif state.get("current_order"):
                    logger.info(f"일상 대화 중 기존 주문 정보 유지: {state.get('current_order')}")
                    state["analysis"] = state.get("current_order")
                
                return state
            
            for item in analysis.get("items", []):
                if "name" in item:
                    menu_name = item["name"]
                    menu_options_result = get_menu_options(menu_name)
                    
                    if menu_options_result.get("status") == "success":
                        required_options = menu_options_result.get("required_options", {})
                        
                        missing_options = []
                        selected_options = set(item.get("options", []))
                        
                        for option_category, options in required_options.items():
                            category_options = [opt["name"] for opt in options]
                            if not any(opt in selected_options for opt in category_options):
                                missing_options.append(option_category)
                        
                        item["missing_required_options"] = missing_options
                        logger.info(f"메뉴 '{menu_name}'의 누락된 필수 옵션: {missing_options}")
            
            state["analysis"] = analysis
            
            any_missing_options = False
            for item in analysis.get("items", []):
                if item.get("missing_required_options", []):
                    any_missing_options = True
                    break
            
            if "clarification_items" in analysis and analysis["clarification_items"]:
                # 필요한 명확화 항목이 있는 경우
                state["response"] = {
                    "message": "주문을 완료하기 위해 추가 정보가 필요합니다.",
                    "needs_clarification": True,
                    "clarification_items": analysis["clarification_items"],
                    "is_casual_conversation": False
                }
                logger.info(f"명확화 항목: {analysis['clarification_items']}")
            else:
                has_items = len(analysis.get("items", [])) > 0
                
                if has_items:
                    if not any_missing_options:
                        response_message = "주문이 추가되었습니다. 더 주문하실 것이 있으신가요?"
                        analysis["clarification_items"] = ["더 주문하실 것이 있으신가요?"]
                        state["response"] = {
                            "message": response_message,
                            "needs_clarification": True,
                            "clarification_items": ["더 주문하실 것이 있으신가요?"],
                            "is_casual_conversation": False
                        }
                    else:
                        response_message = "주문을 계속 진행해주세요."
                        state["response"] = {
                            "message": response_message,
                            "needs_clarification": False,
                            "clarification_items": [],
                            "is_casual_conversation": False
                        }
                else:
                    response_message = "주문하실 메뉴를 말씀해 주세요."
                    state["response"] = {
                        "message": response_message,
                        "needs_clarification": False,
                        "clarification_items": [],
                        "is_casual_conversation": False
                    }
                logger.info(f"주문 처리 상태: 진행 중")
            
            logger.info("주문 분석 완료")
                
        except Exception as e:
            logger.error(f"응답 파싱 오류: {str(e)}", exc_info=True)
            state["response"] = {
                "message": "주문 분석 중 오류가 발생했습니다. 다시 시도해주세요.",
                "needs_clarification": False,
                "clarification_items": [],
                "is_casual_conversation": False
            }
            state["analysis"] = {
                "items": [],
                "total_price": 0,
                "special_requests": "",
                "clarification_items": []
            }
    
    except Exception as e:
        logger.error(f"LLM 처리 중 오류 발생: {str(e)}", exc_info=True)
        state["response"] = {
            "message": "주문 처리 중 오류가 발생했습니다. 다시 시도해주세요.",
            "needs_clarification": False,
            "clarification_items": [],
            "is_casual_conversation": False
        }
        state["analysis"] = {
            "items": [],
            "total_price": 0,
            "special_requests": "",
            "clarification_items": []
        }
    
    return state