from typing import Dict, Any, List, Callable, Optional, Tuple
import re
import logging
import json
from ..state import WorkflowState
from ..tools.menu_tools import get_all_menus, get_menu_info, get_menu_options
from ..tools.vector_store import VectorStore
from ..tools.intent_classifier import IntentClassifier

logger = logging.getLogger("rule_based_node")


KOREAN_PARTICLES = [
    "을", "를", "이", "가", "은", "는", "와", "과", "로", "으로", 
    "의", "에", "에서", "으로부터", "부터", "까지", "하고", "랑", "이랑", "만", "도"
]

class RuleBasedDialogueSystem:
    def __init__(self):
        self.menu_data = self._load_menu_data()
        self.patterns = self._load_patterns()
        self.number_words = self._load_number_words()
        
        self.vector_store = VectorStore()
        self.intent_classifier = IntentClassifier()
        
    def _load_menu_data(self) -> List[Dict[str, Any]]:
        menu_result = get_all_menus()
        if menu_result["status"] != "success":
            logger.warning("메뉴 데이터 로드 실패")
            return []
            
        menu_data = []
        for category in menu_result.get("categories", []):
            for item in category.items:
                menu_data.append({
                    "name": item.name,
                    "base_price": item.base_price,
                    "category": category.name
                })
        return menu_data
        
    def _load_patterns(self) -> Dict[str, List[str]]:
        return {
            "greeting": [
                r"안녕|하이|헬로|좋은\s*(아침|점심|저녁)",
                r"반가워|만나서\s*반가워|반갑|방가|반가워요|반가워용|반갑습니다|방가워요",
                r"어떻게\s*지내|잘\s*지내",
                
                r"오셨|어서오세요|환영|어서\s*와|어서\s*오세요",
                r"뭐\s*있|메뉴\s*알려|메뉴\s*좀|메뉴\s*보여|추천|어떤\s*메뉴|뭐가\s*있",
                r"도와줘|도움|도와주세요|질문|물어볼게|궁금"
            ],
            "farewell": [
                r"안녕히\s*가세요|바이|고마워|감사합니다|감사|땡큐|고마워요",
                r"잘\s*가|다음에\s*봐|다음에\s*만나|또\s*올게요|또\s*봐요|또\s*만나요",
                
                r"수고하세요|수고|잘있어|잘\s*있어요|다음에\s*올게|나중에\s*올게",
                r"끝|완료|주문\s*끝|주문\s*완료|이제\s*됐어|이제\s*됐습니다|주문\s*종료"
            ],
            "order": [
                r"(.*?)\s*(\d+)\s*개?\s*주세요",
                r"(.*?)\s*(\d+)\s*개?\s*주문할게",
                r"(.*?)\s*(\d+)\s*개?\s*요청할게",
                r"(.*?)\s*(\d+)\s*개?\s*줘",
                r"(.*?)\s*(\d+)\s*잔\s*(.+)?",
                r"(.*?)\s*한\s*잔\s*(.+)?",
                r"(.*?)\s*하나\s*(.+)?",
                
                r"(.*?)\s*주세요",
                r"(.*?)\s*줘요?",
                r"(.*?)\s*주문이요",
                r"(.*?)\s*주문할게요?",
                r"(.*?)\s*먹고\s*싶어요?",
                r"(.*?)\s*마시고\s*싶어요?",
                r"(.*?)\s*주문",
                r"(.*?)\s*를?\s*주?문\s*할게",
                r"(.*?)\s*을?\s*주?문\s*할게",
                
                r"(.*?)\s*있나요?",
                r"(.*?)\s*원해요?",
                r"(.*?)\s*드릴게요?",
                r"(.*?)로\s*할게요?",
                r"(.*?)로\s*해주세요",
                r"(.*?)로\s*주세요",
                r"(.*?)로\s*부탁합니다",
                r"(.*?)로\s*부탁드려요?",
                r"(.*?)로\s*부탁",
                r"(.*?)로\s*줘요?"
            ],
            "options": [
                r"(.*?)\s*(따뜻하게|핫|아이스|차갑게)",
                r"(.*?)\s*(레귤러|라지|스몰)",
                r"(.*?)\s*(디카페인|일반)",
                r"(.*?)\s*(휘핑크림\s*추가|휘핑크림\s*없이)",
                
                r"(아이스|핫|따뜻한|차가운|따뜻하게|차갑게|뜨거운|시원한|따뜻하게\s*해주세요|차갑게\s*해주세요)",
                r"(레귤러|라지|스몰|큰|작은|보통|기본|L|S|M|엘|엠|에스|큰\s*거|큰\s*걸로|작은\s*거|작은\s*걸로|보통\s*크기|중간|기본\s*사이즈)",
                r"(디카페인|일반|카페인|디카페인으로|일반으로|카페인\s*없는|카페인\s*있는)",
                r"(휘핑|휘핑크림|크림|휘핑\s*넣어|휘핑\s*추가|크림\s*추가|휘핑\s*빼고|크림\s*빼고|휘핑\s*없이|크림\s*없이)"
            ],
            "size_confirm": [
                r"(큰|라지|large|라아지|L|엘|크게|대형|큰\s*사이즈|라지\s*사이즈|큰\s*거|큰\s*걸로)",
                r"(작은|스몰|small|S|에스|작게|소형|작은\s*사이즈|스몰\s*사이즈|작은\s*거|작은\s*걸로)",
                r"(중간|미디엄|medium|M|엠|보통|레귤러|기본|기본\s*사이즈|보통\s*크기|중간\s*크기)"
            ],
            "temperature_confirm": [
                r"(따뜻한|따뜻하게|핫|hot|뜨거운|뜨겁게|따뜻|더운|뜨거운\s*걸로|따뜻한\s*걸로|따뜻하게\s*해주세요)",
                r"(차가운|아이스|ice|시원한|차갑게|시원하게|차갑|시원|아이스로|차가운\s*걸로|시원한\s*걸로|차갑게\s*해주세요)"
            ],
            "yes_responses": [
                r"(네|예|응|그래|좋아요|좋아|맞아요|맞아|그렇게\s*해줘|그렇게\s*해주세요|OK|오케이|ㅇㅋ|넵|옙)",
                r"(알겠어|알겠습니다|알겠어요|알겠음|ㅇㅇ|웅|어|맞습니다|맞어|맞어요)"
            ],
            "no_responses": [
                r"(아니요|아니|아니오|노|no|아닙니다|아니에요|ㄴㄴ|노노|아뇨)",
                r"(싫어|싫어요|싫습니다|별로|그건\s*아니|다른\s*거|다른\s*걸로)"
            ]
        }
        
    def _load_number_words(self) -> Dict[str, int]:
        return {
            "하나": 1, "한": 1, "한개": 1, "한 개": 1, "한잔": 1, "한 잔": 1,
            "두개": 2, "두 개": 2, "둘": 2, "두잔": 2, "두 잔": 2,
            "세개": 3, "세 개": 3, "셋": 3, "세잔": 3, "세 잔": 3,
            "네개": 4, "네 개": 4, "넷": 4, "네잔": 4, "네 잔": 4,
            "다섯개": 5, "다섯 개": 5, "다섯": 5, "다섯잔": 5, "다섯 잔": 5
        }
    
    def process_input(self, text: str, state: WorkflowState) -> Dict[str, Any]:
        logger.info(f"규칙 기반 노드 입력 처리: '{text}'")
        intent_result = self.intent_classifier.predict(text)
        intent = intent_result["intent"]
        confidence = intent_result["confidence"]
        logger.info(f"의도 분류 결과: {intent} (신뢰도: {confidence:.4f})")
        
        if confidence < 0.3:
            logger.info(f"낮은 신뢰도({confidence:.4f})로 LLM으로 전달")
            return {"should_use_llm": True}
        
        if intent == "인사":
            logger.info("인사말로 인식")
            return self._handle_greeting(text, state)
            
        if intent == "작별":
            logger.info("작별 인사로 인식")
            return self._handle_farewell(text, state)
            
        if intent == "주문":
            order_result = self._extract_order(text)
            if order_result:
                logger.info(f"주문으로 인식: {order_result}")
                return self._handle_order(order_result, state)
            else:
                logger.info("주문으로 분류됐으나 메뉴 정보 추출 실패, LLM으로 전달")
                return {"should_use_llm": True}
            
        if intent == "옵션_선택":
            option_result = self._extract_option(text)
            if option_result:
                logger.info(f"옵션 선택으로 인식: {option_result}")
                return self._handle_option_selection(option_result, state)
            else:
                logger.info("옵션 선택으로 분류됐으나 옵션 정보 추출 실패, LLM으로 전달")
                return {"should_use_llm": True}
        
        similar_response = self.vector_store.find_similar_response(text)
        if similar_response:
            current_items = []
            total_price = 0
            special_requests = ""
            
            if state.get("current_order"):
                current_order = state.get("current_order", {})
                current_items = current_order.get("items", [])
                total_price = current_order.get("total_price", 0)
                special_requests = current_order.get("special_requests", "")
            
            return {
                "is_order_related": False,
                "greeting_response": similar_response["text"],
                "items": current_items,
                "total_price": total_price,
                "special_requests": special_requests,
                "clarification_items": []
            }
        
        logger.info("규칙 기반 처리 실패, LLM으로 전달")
        return {"should_use_llm": True}
        
    def _is_greeting(self, text: str) -> bool:
        return any(re.search(pattern, text) for pattern in self.patterns["greeting"])
        
    def _is_farewell(self, text: str) -> bool:
        return any(re.search(pattern, text) for pattern in self.patterns["farewell"])
        
    def _remove_korean_particles(self, text: str) -> str:
        for particle in KOREAN_PARTICLES:
            if text.endswith(particle) and len(text) > len(particle):
                return text[:-len(particle)]
        return text
    
    def _calculate_menu_similarity(self, menu_name: str, text: str) -> float:
        if menu_name in text or text in menu_name:
            shorter = min(len(menu_name), len(text))
            longer = max(len(menu_name), len(text))
            return shorter / longer
        
        words_menu = set(menu_name.lower().split())
        words_text = set(text.lower().split())
        common_words = words_menu.intersection(words_text)
        
        if common_words:
            return len(common_words) / max(len(words_menu), len(words_text))
            
        return 0.0
    
    def _extract_order(self, text: str) -> Optional[Dict[str, Any]]:
        for pattern in self.patterns["order"]:
            match = re.search(pattern, text)
            
            if match:
                groups = match.groups()
                menu_name = groups[0].strip() if len(groups) > 0 else None
                quantity_str = groups[1] if len(groups) > 1 else None
                quantity = 1  
                if quantity_str:
                    if quantity_str in self.number_words:
                        quantity = self.number_words[quantity_str]
                    else:
                        try:
                            quantity = int(quantity_str)
                        except ValueError:
                            quantity = 1
                
                if not quantity_str and ("하나" in text or "한잔" in text or "한 잔" in text):
                    quantity = 1
                    
                if menu_name:
                    menu_name = self._remove_korean_particles(menu_name)
                    order_info = self._verify_menu(menu_name, quantity, text)
                    if order_info:
                        return order_info
        
        menu_match = self._find_best_matching_menu(text)
        if menu_match:
            menu_name, similarity = menu_match
            quantity = 1  
            quantity_match = re.search(r'(\d+)\s*(잔|개|컵)', text)
            if quantity_match:
                try:
                    quantity = int(quantity_match.group(1))
                except ValueError:
                    quantity = 1
            
            for number_word, number_value in self.number_words.items():
                if number_word in text:
                    quantity = number_value
                    break
            
            order_info = self._verify_menu(menu_name, quantity, text)
            if order_info:
                return order_info
                
        for menu_data in self.menu_data:
            menu_name = menu_data.get("name", "")
            if menu_name and menu_name in text:
                quantity = 1  
                
                quantity_match = re.search(r'(\d+)\s*(잔|개|컵)', text)
                if quantity_match:
                    try:
                        quantity = int(quantity_match.group(1))
                    except ValueError:
                        quantity = 1
                
                for number_word, number_value in self.number_words.items():
                    if number_word in text:
                        quantity = number_value
                        break
                
                options = self._extract_options(text)
                
                return {
                    "menu_name": menu_name,
                    "quantity": quantity,
                    "options": options
                }
                
        return None
    
    def _find_best_matching_menu(self, text: str) -> Optional[Tuple[str, float]]:
        processed_text = self._remove_korean_particles(text.strip())
        
        best_score = 0.0
        best_menu = None
        words = re.findall(r'\w+', processed_text)
        
        for word in words:
            if len(word) < 2:  
                continue
            for menu in self.menu_data:
                menu_name = menu["name"]
                if word in menu_name or menu_name in word:
                    similarity = self._calculate_menu_similarity(menu_name, word)
                    if similarity > best_score:
                        best_score = similarity
                        best_menu = menu_name
        
        for menu in self.menu_data:
            menu_name = menu["name"]
            similarity = self._calculate_menu_similarity(menu_name, processed_text)
            
            if similarity > best_score:
                best_score = similarity
                best_menu = menu_name
        
        if best_score >= 0.3 and best_menu:
            return (best_menu, best_score)
            
        return None
        
    def _verify_menu(self, menu_name: str, quantity: int, text: str) -> Optional[Dict[str, Any]]:
        menu_info = get_menu_info(menu_name)
        if menu_info["status"] != "success":
            logger.info(f"메뉴 '{menu_name}' 정확히 일치하지 않음, 유사 매칭 시도")
            best_match = None
            best_score = 0.0
            
            for menu in self.menu_data:
                similarity = self._calculate_menu_similarity(menu["name"], menu_name)
                if similarity > best_score:
                    best_score = similarity
                    best_match = menu["name"]
            
            if best_match and best_score >= 0.5:
                menu_info = get_menu_info(best_match)
                if menu_info["status"] == "success":
                    menu_name = best_match
                    logger.info(f"유사 메뉴 발견: {menu_name} (유사도: {best_score:.4f})")
                        
            if menu_info["status"] != "success":
                return None
                
        options = self._extract_options(text)
        
        return {
            "menu_name": menu_name,
            "quantity": quantity,
            "options": options
        }
        
    def _is_option_selection(self, text: str) -> bool:
        return any(re.search(pattern, text) for pattern in self.patterns["options"])
        
    def _extract_option(self, text: str) -> Optional[Dict[str, Any]]:
        options = self._extract_options(text)
        
        menu_name = None
        best_match = None
        best_score = 0.0
        
        for menu in self.menu_data:
            if menu["name"] in text:
                menu_name = menu["name"]
                break
        
        if not menu_name:
            processed_text = self._remove_korean_particles(text.strip())
            words = re.findall(r'\w+', processed_text)
            for word in words:
                if len(word) < 2:  
                    continue
                    
                for menu in self.menu_data:
                    similarity = self._calculate_menu_similarity(menu["name"], word)
                    if similarity > best_score:
                        best_score = similarity
                        best_match = menu["name"]
            
            if best_score >= 0.5 and best_match:
                menu_name = best_match
                logger.info(f"옵션 처리에서 유사도 기반 메뉴 매칭: {best_match} (점수: {best_score:.4f})")
                
        if not menu_name and not options:
            return None
            
        return {
            "menu_name": menu_name,
            "options": options
        }
        
    def _extract_options(self, text: str) -> List[str]:
        options = []
        
        if re.search(r'따뜻|뜨겁|핫|hot|따뜻하게|뜨거운|따뜻한|더운|따뜻하게\s*해|따듯', text.lower()):
            options.append("핫")
        elif re.search(r'차갑|시원|아이스|ice|차게|시원하게|찬|차가운|아이스로|시원한|차갑게\s*해', text.lower()):
            options.append("아이스")
            
        if re.search(r'크게|큰|라지|large|라아지|크게|큰\s*걸로|크게\s*주세요|L사이즈|L\s*사이즈|대형|라아지|라지\s*사이즈|라지로', text.lower()):
            options.append("라지")
        elif re.search(r'작게|작은|스몰|small|작은\s*걸로|작게\s*주세요|S사이즈|S\s*사이즈|소형|스몰\s*사이즈|스몰로', text.lower()):
            options.append("레귤러")
        elif re.search(r'중간|보통|일반|medium|레귤러|보통\s*크기|중간\s*크기|기본|기본\s*사이즈|M\s*사이즈|미디엄|m\s*사이즈|미디엄\s*사이즈|보통으로', text.lower()):
            options.append("레귤러")
            
        if re.search(r'디카페인|디카페|디카페인으로|디카페인\s*으로|디카페인\s*걸로|카페인\s*없는|카페인\s*제거', text.lower()):
            options.append("디카페인")
        elif re.search(r'일반|원래|카페인|카페인\s*있는|카페인\s*넣은|일반으로', text.lower()):
            options.append("일반")
            
        if re.search(r'휘핑|휘핑크림|휘핑크림\s*추가|크림\s*추가|휘핑\s*추가|휘핑\s*넣어|크림\s*넣어|휘핑\s*올려|크림\s*올려|토핑', text.lower()):
            options.append("휘핑크림 추가")
        elif re.search(r'휘핑\s*없이|크림\s*없이|휘핑\s*빼|크림\s*빼|토핑\s*없이', text.lower()):
            options.append("휘핑크림 없음")
        
        for pattern in self.patterns["options"]:
            matches = re.findall(pattern, text)
            if matches:
                for match in matches:
                    if isinstance(match, tuple):
                        option_text = match[1] if len(match) > 1 else match[0]
                    else:
                        option_text = match
                        
                    if re.search(r'핫|따뜻|뜨|더운', option_text):
                        if "핫" not in options:
                            options.append("핫")
                    elif re.search(r'아이스|차|시원|찬', option_text):
                        if "아이스" not in options:
                            options.append("아이스")
                            
                    if re.search(r'라지|큰|L|대|크', option_text):
                        if "라지" not in options:
                            options.append("라지")
                    elif re.search(r'레귤러|보통|중간|M|기본', option_text):
                        if "레귤러" not in options:
                            options.append("레귤러")
                    elif re.search(r'스몰|작|S|소', option_text):
                        if "레귤러" not in options:  
                            options.append("레귤러")
                    
                    if re.search(r'디카페인|디카페|카페인\s*없', option_text):
                        if "디카페인" not in options:
                            options.append("디카페인")
                    elif re.search(r'일반|카페인|원래', option_text):
                        if "일반" not in options:
                            options.append("일반")
                    
                    if re.search(r'휘핑.*추가|크림.*추가|휘핑.*넣|크림.*넣|토핑', option_text):
                        if "휘핑크림 추가" not in options:
                            options.append("휘핑크림 추가")
                    elif re.search(r'휘핑.*없|크림.*없|휘핑.*빼|크림.*빼|토핑.*없', option_text):
                        if "휘핑크림 없음" not in options:
                            options.append("휘핑크림 없음")
        
        for pattern in self.patterns.get("size_confirm", []):
            if re.search(pattern, text.lower()):
                if re.search(self.patterns["size_confirm"][0], text.lower()):  
                    if "라지" not in options:
                        options.append("라지")
                elif re.search(self.patterns["size_confirm"][1], text.lower()) or re.search(self.patterns["size_confirm"][2], text.lower()):  
                    if "라지" not in options and "레귤러" not in options:
                        options.append("레귤러")
        
        for pattern in self.patterns.get("temperature_confirm", []):
            if re.search(pattern, text.lower()):
                if re.search(self.patterns["temperature_confirm"][0], text.lower()):  
                    if "핫" not in options and "아이스" not in options:
                        options.append("핫")
                elif re.search(self.patterns["temperature_confirm"][1], text.lower()):  
                    if "핫" not in options and "아이스" not in options:
                        options.append("아이스")
        return options
        
    def _handle_greeting(self, text: str, state: Optional[WorkflowState] = None) -> Dict[str, Any]:
        response = self.vector_store.get_response_by_type("greeting")
        greeting_text = "안녕하세요! 무엇을 도와드릴까요?"
        
        if response:
            greeting_text = response["text"]
        
        current_items = []
        total_price = 0
        special_requests = ""
        
        if state and state.get("current_order"):
            current_order = state.get("current_order", {})
            current_items = current_order.get("items", [])
            total_price = current_order.get("total_price", 0)
            special_requests = current_order.get("special_requests", "")
        
        return {
            "is_order_related": False,
            "greeting_response": greeting_text,
            "items": current_items,
            "total_price": total_price,
            "special_requests": special_requests,
            "clarification_items": []
        }
        
    def _handle_farewell(self, text: str, state: Optional[WorkflowState] = None) -> Dict[str, Any]:
        response = self.vector_store.get_response_by_type("farewell")
        farewell_text = "이용해 주셔서 감사합니다. 좋은 하루 되세요!"
        
        if response:
            farewell_text = response["text"]
        
        current_items = []
        total_price = 0
        special_requests = ""
        
        if state and state.get("current_order"):
            current_order = state.get("current_order", {})
            current_items = current_order.get("items", [])
            total_price = current_order.get("total_price", 0)
            special_requests = current_order.get("special_requests", "")
        
        return {
            "is_order_related": False,
            "greeting_response": farewell_text,
            "items": current_items,
            "total_price": total_price,
            "special_requests": special_requests,
            "clarification_items": []
        }
        
    def _handle_order(self, order_result: Dict[str, Any], state: WorkflowState) -> Dict[str, Any]:
        menu_name = order_result["menu_name"]
        quantity = order_result["quantity"]
        options = order_result["options"]
        
        menu_info = get_menu_info(menu_name)
        if menu_info["status"] != "success":
            return {"should_use_llm": True}
            
        menu = menu_info["menu"]
        
        missing_options = self._check_missing_options(menu, options)
        
        new_item = {
            "name": menu_name,
            "quantity": quantity,
            "options": options,
            "missing_required_options": missing_options,
            "price": menu["base_price"]
        }
        current_order = state.get("current_order", {})
        items = current_order.get("items", []) if current_order else []
        
        updated_items = items.copy()  
        updated_items.append(new_item)
        total_price = sum(item["price"] * item["quantity"] for item in updated_items)
        
        if missing_options:
            clarification_items = self._generate_clarification_items(menu_name, missing_options)
            return {
                "is_order_related": True,
                "items": updated_items,  
                "total_price": total_price,
                "special_requests": current_order.get("special_requests", "") if current_order else "",
                "clarification_items": clarification_items
            }
        else:
            response = self.vector_store.get_response_by_type("additional_order")
            additional_order_text = "더 주문하실 것이 있으신가요?"
            
            if response:
                additional_order_text = response["text"]
                
            return {
                "is_order_related": True,
                "items": updated_items,  
                "total_price": total_price,
                "special_requests": current_order.get("special_requests", "") if current_order else "",
                "clarification_items": [additional_order_text]
            }
            
    def _handle_option_selection(self, option_result: Dict[str, Any], state: WorkflowState) -> Dict[str, Any]:
        options = option_result["options"]
        menu_name = option_result["menu_name"]
        
        current_order = state.get("current_order", {})
        if not current_order or "items" not in current_order:
            logger.warning("현재 주문 정보가 없음")
            return {"should_use_llm": True}
            
        if not menu_name:
            pending_clarifications = state.get("pending_clarifications", [])
            if pending_clarifications:
                for clarification in pending_clarifications:
                    menu_match = re.search(r'([가-힣A-Za-z\s]+)을', clarification)
                    if menu_match:
                        menu_name = menu_match.group(1).strip()
                        break
            
            if not menu_name and current_order.get("items", []):
                menu_name = current_order["items"][-1]["name"]
                
        if not menu_name:
            logger.warning("옵션을 적용할 메뉴를 찾을 수 없음")
            return {"should_use_llm": True}
            
        items = current_order.get("items", [])
        updated = False
        
        for item in items:
            if item["name"] == menu_name:
                for option in options:
                    if option not in item["options"]:
                        item["options"].append(option)
                
                menu_info = get_menu_info(menu_name)
                if menu_info["status"] == "success":
                    menu = menu_info["menu"]
                    item["missing_required_options"] = self._check_missing_options(menu, item["options"])
                
                updated = True
                break
                
        if not updated:
            logger.warning(f"메뉴 '{menu_name}'을 현재 주문에서 찾을 수 없음")
            return {"should_use_llm": True}
            
        missing_options = []
        for item in items:
            if item.get("missing_required_options", []):
                missing_options.extend(item["missing_required_options"])
                
        if missing_options:
            clarification_items = []
            for item in items:
                if item.get("missing_required_options", []):
                    clarification_items.extend(
                        self._generate_clarification_items(item["name"], item["missing_required_options"])
                    )
                    break  
                    
            return {
                "is_order_related": True,
                "items": items,
                "total_price": sum(item["price"] * item["quantity"] for item in items),
                "special_requests": current_order.get("special_requests", "") if current_order else "",
                "clarification_items": clarification_items[:1]  
            }
        else:
            response = self.vector_store.get_response_by_type("additional_order")
            additional_order_text = "더 주문하실 것이 있으신가요?"
            
            if response:
                additional_order_text = response["text"]
                
            return {
                "is_order_related": True,
                "items": items,
                "total_price": sum(item["price"] * item["quantity"] for item in items),
                "special_requests": current_order.get("special_requests", "") if current_order else "",
                "clarification_items": [additional_order_text]
            }
            
    def _check_missing_options(self, menu: Dict[str, Any], selected_options: List[str]) -> List[str]:
        missing_options = []
        required_options = menu.get("required_options", {})
        
        for option_category, options in required_options.items():
            category_options = [opt["name"] for opt in options]
            if not any(opt in selected_options for opt in category_options):
                missing_options.append(option_category)
                
        return missing_options
        
    def _generate_clarification_items(self, menu_name: str, missing_options: List[str]) -> List[str]:
        clarification_items = []
        for option_category in missing_options:
            if option_category == "온도":
                clarification = self.vector_store.get_clarification_template(menu_name, "온도")
                if clarification:
                    clarification_items.append(clarification)
                else:
                    clarification_items.append(f"{menu_name}을 따뜻한 음료로 드릴까요, 차가운 음료로 드릴까요?")
            elif option_category == "크기":
                clarification = self.vector_store.get_clarification_template(menu_name, "크기")
                if clarification:
                    clarification_items.append(clarification)
                else:
                    clarification_items.append(f"{menu_name}을 레귤러 사이즈로 드릴까요, 라지 사이즈로 드릴까요?")
                
        return clarification_items
        
def process_dialogue(state: WorkflowState) -> Dict[str, Any]:
    try:
        dialogue_system = RuleBasedDialogueSystem()
        text_input = state.get('text', '')
        
        logger.info(f"규칙 기반 대화 처리 시작: 텍스트='{text_input}'")
        pending_clarifications = state.get("pending_clarifications", [])
        current_order = state.get("current_order", {})
        
        if current_order and "items" in current_order:
            logger.info(f"현재 주문 항목: {len(current_order['items'])}개")
            for i, item in enumerate(current_order["items"]):
                logger.info(f"주문 항목 {i+1}: {item['name']} x {item['quantity']}, 옵션: {item.get('options', [])}")
        
        state["pending_clarifications_resolved"] = False
        
        order_result = None
        if text_input:
            order_result = dialogue_system._extract_order(text_input)
            
        if order_result:
            logger.info(f"새 주문 감지: {order_result}")
            
            state["pending_clarifications_resolved"] = True
            result = dialogue_system._handle_order(order_result, state)
            if result.get("should_use_llm", False):
                logger.info("새 주문 처리에 실패, LLM으로 전달")
                state["rule_based_result"] = {"success": False}
                return state
            
            state["analysis"] = {
                "items": result.get("items", []),
                "total_price": result.get("total_price", 0),
                "special_requests": result.get("special_requests", ""),
                "clarification_items": result.get("clarification_items", [])
            }
            
            needs_clarification = bool(result.get("clarification_items", []))
            
            if needs_clarification:
                state["response"] = {
                    "message": "주문을 완료하기 위해 추가 정보가 필요합니다.",
                    "needs_clarification": True,
                    "clarification_items": result.get("clarification_items", []),
                    "is_casual_conversation": False,
                    "should_continue_ordering": True
                }
                logger.info(f"명확화 항목: {result.get('clarification_items', [])}")
            else:
                state["response"] = {
                    "message": "주문이 추가되었습니다. 더 주문하실 것이 있으신가요?",
                    "needs_clarification": True,
                    "clarification_items": ["더 주문하실 것이 있으신가요?"],
                    "is_casual_conversation": False,
                    "should_continue_ordering": True,
                    "asking_for_more_items": True
                }
            
            state["rule_based_result"] = {"success": True}
            logger.info("새 주문 처리 완료")
            return state
        
        if pending_clarifications and text_input:
            logger.info(f"명확화 진행 중: {pending_clarifications[0]}")
            clarification = pending_clarifications[0]
            
            if "더 주문" in clarification or "추가 주문" in clarification:
                logger.info("추가 주문 관련 명확화 감지: 새 주문 처리로 전환")
                
                state["pending_clarifications_resolved"] = True
                
                order_result = dialogue_system._extract_order(text_input)
                if order_result:
                    logger.info(f"추가 주문 감지: {order_result}")
                    result = dialogue_system._handle_order(order_result, state)
                    
                    if result.get("should_use_llm", False):
                        logger.info("추가 주문 처리에 실패, LLM으로 전달")
                        state["rule_based_result"] = {"success": False}
                        return state
                    
                    state["analysis"] = {
                        "items": result.get("items", []),
                        "total_price": result.get("total_price", 0),
                        "special_requests": result.get("special_requests", ""),
                        "clarification_items": result.get("clarification_items", [])
                    }
                    
                    needs_clarification = bool(result.get("clarification_items", []))
                    
                    if needs_clarification:
                        state["response"] = {
                            "message": "주문을 완료하기 위해 추가 정보가 필요합니다.",
                            "needs_clarification": True,
                            "clarification_items": result.get("clarification_items", []),
                            "is_casual_conversation": False,
                            "should_continue_ordering": True
                        }
                        logger.info(f"명확화 항목: {result.get('clarification_items', [])}")
                    else:
                        state["response"] = {
                            "message": "주문이 추가되었습니다. 더 주문하실 것이 있으신가요?",
                            "needs_clarification": True,
                            "clarification_items": ["더 주문하실 것이 있으신가요?"],
                            "is_casual_conversation": False,
                            "should_continue_ordering": True,
                            "asking_for_more_items": True
                        }
                    
                    state["rule_based_result"] = {"success": True}
                    logger.info("추가 주문 처리 완료")
                    return state
                else:
                    if "네" in text_input.lower() or "예" in text_input.lower() or "더" in text_input.lower() or "추가" in text_input.lower():
                        logger.info("추가 주문 의사 확인됨, 명확화 항목 해결")
                        state["pending_clarifications_resolved"] = True
                        state["response"] = {
                            "message": "어떤 메뉴를 더 주문하시겠어요?",
                            "needs_clarification": False,
                            "clarification_items": [],
                            "is_casual_conversation": False,
                            "should_continue_ordering": True
                        }
                        state["rule_based_result"] = {"success": True}
                        return state
                    elif "아니" in text_input.lower() or "없" in text_input.lower() or "괜찮" in text_input.lower():
                        logger.info("추가 주문 의사 없음, 주문 완료")
                        state["pending_clarifications_resolved"] = True
                        state["response"] = {
                            "message": "주문이 완료되었습니다. 감사합니다!",
                            "needs_clarification": False,
                            "clarification_items": [],
                            "is_casual_conversation": False,
                            "should_continue_ordering": False,
                            "order_complete": True
                        }
                        state["rule_based_result"] = {"success": True}
                        return state
                    
            menu_name = None
            option_type = None
            
            menu_match = re.search(r'([가-힣A-Za-z\s]+)(을|를|에)', clarification)
            if menu_match:
                menu_name = menu_match.group(1).strip()
                
            if "온도" in clarification or "따뜻" in clarification or "차가" in clarification or "아이스" in clarification or "핫" in clarification:
                option_type = "온도"
            elif "크기" in clarification or "사이즈" in clarification or "레귤러" in clarification or "라지" in clarification:
                option_type = "크기"
                
            logger.info(f"명확화 분석 결과: 메뉴={menu_name}, 옵션 유형={option_type}")
            
            extracted_options = dialogue_system._extract_options(text_input)
            
            if extracted_options:
                logger.info(f"명확화 응답에서 옵션 추출됨: {extracted_options}")
                if menu_name:
                    option_selection = {
                        "menu_name": menu_name,
                        "options": extracted_options
                    }
                    result = dialogue_system._handle_option_selection(option_selection, state)
                    
                    state["pending_clarifications_resolved"] = True
                    
                    if result.get("should_use_llm", False):
                        logger.info("명확화 처리에 실패, LLM으로 전달")
                        state["rule_based_result"] = {"success": False}
                        return state
                    
                    state["analysis"] = {
                        "items": result.get("items", []),
                        "total_price": result.get("total_price", 0),
                        "special_requests": result.get("special_requests", ""),
                        "clarification_items": result.get("clarification_items", [])
                    }
                    
                    needs_clarification = bool(result.get("clarification_items", []))
                    
                    if needs_clarification:
                        state["response"] = {
                            "message": "주문을 완료하기 위해 추가 정보가 필요합니다.",
                            "needs_clarification": True,
                            "clarification_items": result.get("clarification_items", []),
                            "is_casual_conversation": False,
                            "should_continue_ordering": True
                        }
                        logger.info(f"명확화 항목: {result.get('clarification_items', [])}")
                    else:
                        state["response"] = {
                            "message": "옵션이 선택되었습니다. 더 주문하실 것이 있으신가요?",
                            "needs_clarification": True,
                            "clarification_items": ["더 주문하실 것이 있으신가요?"],
                            "is_casual_conversation": False,
                            "should_continue_ordering": True,
                            "asking_for_more_items": True
                        }
                    state["rule_based_result"] = {"success": True}
                    logger.info("명확화 응답 처리 완료")
                    return state
                else:
                    if current_order and current_order.get("items", []):
                        menu_name = current_order["items"][-1]["name"]
                        logger.info(f"마지막 주문 항목의 메뉴 이름 사용: '{menu_name}'")
                        
                        option_selection = {
                            "menu_name": menu_name,
                            "options": extracted_options
                        }
                        result = dialogue_system._handle_option_selection(option_selection, state)
                        
                        state["pending_clarifications_resolved"] = True
                        
                        if result.get("should_use_llm", False):
                            logger.info("명확화 처리에 실패, LLM으로 전달")
                            state["rule_based_result"] = {"success": False}
                            return state
                        
                        state["analysis"] = {
                            "items": result.get("items", []),
                            "total_price": result.get("total_price", 0),
                            "special_requests": result.get("special_requests", ""),
                            "clarification_items": result.get("clarification_items", [])
                        }
                        
                        logger.info(f"명확화 처리 후 주문 항목 수: {len(result.get('items', []))}")
                        
                        needs_clarification = bool(result.get("clarification_items", []))
                        
                        if needs_clarification:
                            state["response"] = {
                                "message": "주문을 완료하기 위해 추가 정보가 필요합니다.",
                                "needs_clarification": True,
                                "clarification_items": result.get("clarification_items", []),
                                "is_casual_conversation": False,
                                "should_continue_ordering": True
                            }
                            logger.info(f"명확화 항목: {result.get('clarification_items', [])}")
                        else:
                            state["response"] = {
                                "message": "옵션이 선택되었습니다. 더 주문하실 것이 있으신가요?",
                                "needs_clarification": True,
                                "clarification_items": ["더 주문하실 것이 있으신가요?"],
                                "is_casual_conversation": False,
                                "should_continue_ordering": True,
                                "asking_for_more_items": True
                            }
                        
                        state["rule_based_result"] = {"success": True}
                        logger.info("명확화 응답 처리 완료")
                        return state
        
        intent_result = state.get("intent_classification", {})
        intent = intent_result.get("intent", "일상_대화")
        confidence = intent_result.get("confidence", 0.0)
        
        logger.info(f"의도 분류 결과 활용: 의도={intent}, 신뢰도={confidence:.4f}")
        
        if confidence < 0.3:
            logger.info(f"낮은 의도 분류 신뢰도({confidence:.4f})로 LLM으로 전달")
            state["rule_based_result"] = {"success": False}
            return state
            
        if intent == "인사":
            logger.info("인사말 의도 처리")
            result = dialogue_system._handle_greeting(text_input, state)
        elif intent == "작별":
            logger.info("작별 인사 의도 처리")
            result = dialogue_system._handle_farewell(text_input, state)
        elif intent == "주문":
            logger.info("주문 의도 처리")
            order_result = dialogue_system._extract_order(text_input)
            if order_result:
                result = dialogue_system._handle_order(order_result, state)
            else:
                logger.info("주문 정보 추출 실패, LLM으로 전달")
                state["rule_based_result"] = {"success": False}
                return state
        elif intent == "옵션_선택":
            logger.info("옵션 선택 의도 처리")
            option_result = dialogue_system._extract_option(text_input)
            if option_result:
                result = dialogue_system._handle_option_selection(option_result, state)
            else:
                logger.info("옵션 정보 추출 실패, LLM으로 전달")
                state["rule_based_result"] = {"success": False}
                return state
        else:
            logger.info("일상 대화 의도 처리")
            similar_response = dialogue_system.vector_store.find_similar_response(text_input)
            if similar_response:
                current_order = state.get("current_order", {})
                result = {
                    "is_order_related": False,
                    "greeting_response": similar_response["text"],
                    "items": current_order.get("items", []),
                    "total_price": current_order.get("total_price", 0),
                    "special_requests": current_order.get("special_requests", ""),
                    "clarification_items": []
                }
            else:
                logger.info("적절한 응답을 찾을 수 없어 LLM으로 전달")
                state["rule_based_result"] = {"success": False}
                return state
                
        if result.get("should_use_llm", False):
            logger.info("규칙 기반 처리가 LLM 사용을 요청, LLM으로 전달")
            state["rule_based_result"] = {"success": False}
            return state
            
        if not result.get("is_order_related", True) and state.get("current_order"):
            state["analysis"] = state.get("current_order", {})
        else:
            state["analysis"] = {
                "items": result.get("items", []),
                "total_price": result.get("total_price", 0),
                "special_requests": result.get("special_requests", ""),
                "clarification_items": result.get("clarification_items", [])
            }
        
        is_casual = not result.get("is_order_related", True)
        needs_clarification = bool(result.get("clarification_items", []))
        
        if is_casual:
            state["response"] = {
                "message": result.get("greeting_response", "무엇을 도와드릴까요?"),
                "needs_clarification": False,
                "clarification_items": [],
                "is_casual_conversation": True,
                "should_continue_ordering": True  
            }
        else:
            if needs_clarification:
                state["response"] = {
                    "message": "주문을 완료하기 위해 추가 정보가 필요합니다.",
                    "needs_clarification": True,
                    "clarification_items": result.get("clarification_items", []),
                    "is_casual_conversation": False,
                    "should_continue_ordering": True  
                }
                logger.info(f"명확화 항목: {result.get('clarification_items', [])}")
            else:
                state["response"] = {
                    "message": "주문이 추가되었습니다. 더 주문하실 것이 있으신가요?",
                    "needs_clarification": True,
                    "clarification_items": ["더 주문하실 것이 있으신가요?"],
                    "is_casual_conversation": False,
                    "should_continue_ordering": True,  
                    "asking_for_more_items": True
                }
        
        state["rule_based_result"] = {"success": True}
        logger.info("규칙 기반 대화 처리 완료")
        return state
        
    except Exception as e:
        logger.error(f"규칙 기반 대화 처리 중 오류 발생: {str(e)}", exc_info=True)
        state["rule_based_result"] = {"success": False}
        return state

def should_use_llm(state: WorkflowState) -> str:
    rule_based_result = state.get("rule_based_result", {})
    if not rule_based_result.get("success", False):
        return "analyze_order"
    return "END"
