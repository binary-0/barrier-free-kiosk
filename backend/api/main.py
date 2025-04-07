from fastapi import FastAPI, UploadFile, File, HTTPException, Header, Body
from fastapi.middleware.cors import CORSMiddleware
import shutil
import uuid
import sys
import os
import logging
from pathlib import Path
import time
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("api.log")
    ]
)
logger = logging.getLogger("api")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.langgraph.graph import create_order_analysis_workflow
from core.langgraph.state import WorkflowState
from core.db import init_db, populate_db, get_menu_categories
from core.models.order import OrderSessionManager
from core.langgraph.nodes.stt_node import load_model

app = FastAPI()
load_model()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 임시 파일 저장
UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def cleanup_old_files():
    try:
        current_time = time.time()
        for file_path in UPLOAD_DIR.glob('*.webm'):
            file_age = current_time - file_path.stat().st_mtime
            if file_age > 3600:  # 1시간(3600초) 이상 된 파일
                file_path.unlink()
                logger.info(f"오래된 임시 파일 삭제: {file_path}")
    except Exception as e:
        logger.error(f"임시 파일 정리 중 오류: {str(e)}")

cleanup_old_files()

init_db()
populate_db()

session_manager = OrderSessionManager()

order_analysis_chain = create_order_analysis_workflow()

@app.get("/menu")
async def get_menu():
    try:
        return {
            "status": "success",
            "data": get_menu_categories()
        }
    except Exception as e:
        logger.error(f"메뉴 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze-order")
async def analyze_order_endpoint(
    audio_file: UploadFile = File(...),
    session_id: str = Header(None)
):
    try:
        logger.info(f"음성 분석 요청 수신: 파일={audio_file.filename}, 세션ID={session_id}")
        
        if not session_id:
            session_id = str(uuid.uuid4())
            logger.info(f"새 세션 생성: {session_id}")
        
        session = session_manager.get_session(session_id)
        if not session:
            logger.info(f"기존 세션 없음, 새로 생성: {session_id}")
            session = session_manager.create_session(session_id)
        
        file_contents = await audio_file.read()
        await audio_file.seek(0) 
        
        if len(file_contents) == 0:
            logger.error("빈 오디오 파일 수신")
            raise HTTPException(status_code=400, detail="Empty audio file received")
        
        logger.info(f"수신된 오디오 파일 크기: {len(file_contents)} bytes")
        
        timestamp = int(time.time())
        unique_filename = f"{session_id}_{timestamp}.webm"
        temp_file_path = UPLOAD_DIR / unique_filename
    
        with temp_file_path.open("wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        logger.info(f"임시 파일 저장 완료: {temp_file_path}")
        
        session_manager.add_conversation(session_id, "user", "음성 주문")
        
        initial_state: WorkflowState = {
            "audio_path": str(temp_file_path),
            "text": "",
            "analysis": None,
            "response": None,
            "session_id": session_id,
            "conversation_history": session.conversation_history,
            "pending_clarifications": session.pending_clarifications,
            "current_order": session.current_order
        }
        
        # LangGraph 실행
        logger.info("LangGraph 워크플로우 실행 시작")
        try:
            result = order_analysis_chain.invoke(initial_state)
            if not result:
                logger.error("LangGraph 워크플로우가 None을 반환했습니다.")
                raise ValueError("워크플로우 실행 결과가 없습니다.")
                
            logger.info(f"LangGraph 워크플로우 실행 완료: 인식된 텍스트={result.get('text', '')}")
            
            try:
                temp_file_path.unlink()
                logger.info(f"임시 파일 삭제 완료: {temp_file_path}")
            except Exception as e:
                logger.warning(f"임시 파일 삭제 실패: {str(e)}")
            
            # 세션 업데이트
            if not result.get("analysis"):
                logger.warning("분석 결과가 없습니다. 기본값 사용")
                result["analysis"] = {
                    "items": [],
                    "total_price": 0,
                    "special_requests": ""
                }
            
            # 일상 대화이고 이전 주문 정보가 있는 경우 기존 주문 정보 유지
            if result["response"].get("is_casual_conversation", False) and session.current_order:
                logger.info(f"일상 대화 감지: 기존 주문 정보 유지 (세션 ID: {session_id})")
                result["analysis"] = session.current_order
            
            # 세션 업데이트 (주문 정보가 변경된 경우에만)
            session_manager.update_session(session_id, result["analysis"])
            logger.info(f"세션 업데이트 완료 (세션 ID: {session_id})")
            
            # 대화 기록에 시스템 응답 추가
            if not result.get("response"):
                logger.warning("응답이 없습니다. 기본 응답 사용")
                result["response"] = {
                    "message": "주문 처리 중 오류가 발생했습니다. 다시 시도해주세요.",
                    "needs_clarification": False,
                    "clarification_items": []
                }
                
            system_response = result["response"]["message"]
            session_manager.add_conversation(session_id, "assistant", system_response)
            logger.info(f"시스템 응답: {system_response}")
            
            # clarification 처리
            if result["response"]["needs_clarification"]:
                # 명확화 항목 초기화 후 새로 추가
                session_manager.clear_pending_clarifications(session_id)
                # 첫 번째 명확화 항목만 추가 (한 번에 하나만 처리)
                if result["response"]["clarification_items"]:
                    first_item = result["response"]["clarification_items"][0]
                    session_manager.add_pending_clarification(session_id, first_item)
                    logger.info(f"명확화 항목 추가: {first_item}")
                    
                    # 프론트엔드로 하나의 명확화 항목만 전송
                    result["response"]["clarification_items"] = [first_item]
            else:
                session_manager.clear_pending_clarifications(session_id)
            
            # 명확화가 필요한 경우, 응답 메시지를 첫 번째 명확화 항목으로 변경
            if result["response"]["needs_clarification"] and result["response"]["clarification_items"]:
                # 일상 대화가 아닌 경우에만 메시지를 명확화 항목으로 변경
                if not result["response"].get("is_casual_conversation", False):
                    result["response"]["message"] = result["response"]["clarification_items"][0]
            
            response_data = {
                "status": "success",
                "session_id": session_id,
                "data": {
                    "order": result["analysis"],
                    "message": result["response"]["message"],
                    "needs_clarification": result["response"]["needs_clarification"],
                    "clarification_items": result["response"]["clarification_items"],
                    "is_casual_conversation": result["response"].get("is_casual_conversation", False),
                    "order_complete": False,
                    "should_continue_ordering": True,
                    "asking_for_more_items": False
                }
            }
            
            logger.info(f"음성 분석 응답 전송: 세션ID={session_id}")
            return response_data
        except ValueError as e:
            logger.error(f"LLM 응답 파싱 오류: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"분석 중 예상치 못한 오류: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        logger.error(f"분석 중 예상치 못한 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/respond-clarification")
async def respond_to_clarification(
    audio_file: UploadFile = File(...),
    session_id: str = Header(...)
):
    try:
        logger.info(f"음성 명확화 응답 수신: 파일={audio_file.filename}, 세션ID={session_id}")
        
        session = session_manager.get_session(session_id)
        if not session:
            logger.error(f"세션을 찾을 수 없음: {session_id}")
            raise HTTPException(status_code=404, detail="Session not found")
        
        file_contents = await audio_file.read()
        await audio_file.seek(0) 
        
        if len(file_contents) == 0:
            logger.error("빈 오디오 파일 수신")
            raise HTTPException(status_code=400, detail="Empty audio file received")
        
        logger.info(f"수신된 오디오 파일 크기: {len(file_contents)} bytes")
        
        timestamp = int(time.time())
        unique_filename = f"{session_id}_clarification_{timestamp}.webm"
        temp_file_path = UPLOAD_DIR / unique_filename
        
        with temp_file_path.open("wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        logger.info(f"임시 파일 저장 완료: {temp_file_path}")
        
        conversation_history = session.conversation_history
        pending_clarifications = session.pending_clarifications
        
        if not pending_clarifications:
            logger.warning("처리할 명확화 항목이 없습니다")
            
            try:
                temp_file_path.unlink()
                logger.info(f"임시 파일 삭제 완료: {temp_file_path}")
            except Exception as e:
                logger.warning(f"임시 파일 삭제 실패: {str(e)}")
                
            return {
                "status": "success",
                "session_id": session_id,
                "data": {
                    "order": session.current_order,
                    "message": "더 주문하실 것이 있으신가요?",
                    "needs_clarification": True,
                    "clarification_items": ["더 주문하실 것이 있으신가요?"],
                    "is_casual_conversation": False,
                    "order_complete": False,
                    "should_continue_ordering": True,
                    "asking_for_more_items": False
                }
            }
        
        initial_state: WorkflowState = {
            "audio_path": str(temp_file_path),
            "text": "",
            "analysis": session.current_order,
            "response": None,
            "session_id": session_id,
            "conversation_history": conversation_history,
            "pending_clarifications": pending_clarifications,
            "current_order": session.current_order
        }
        
        logger.info("명확화 응답 처리를 위한 LangGraph 워크플로우 실행 시작")
        try:
            result = order_analysis_chain.invoke(initial_state)
            
            if not result:
                logger.error("LangGraph 워크플로우가 None을 반환했습니다.")
                raise ValueError("워크플로우 실행 결과가 없습니다.")
                
            logger.info(f"LangGraph 워크플로우 실행 완료: 인식된 텍스트={result.get('text', '')}")
            
            try:
                temp_file_path.unlink()
                logger.info(f"임시 파일 삭제 완료: {temp_file_path}")
            except Exception as e:
                logger.warning(f"임시 파일 삭제 실패: {str(e)}")
            
            if not result.get("analysis"):
                logger.warning("분석 결과가 없습니다. 기존 주문 정보 유지")
                result["analysis"] = session.current_order or {
                    "items": [],
                    "total_price": 0,
                    "special_requests": ""
                }
            
            if result["response"].get("is_casual_conversation", False) and session.current_order:
                logger.info(f"명확화 중 일상 대화 감지: 기존 주문 정보 유지 (세션 ID: {session_id})")
                result["analysis"] = session.current_order
            
            session_manager.update_session(session_id, result["analysis"])
            logger.info(f"명확화 응답 후 세션 업데이트 완료 (세션 ID: {session_id})")
            
            if result.get("text"):
                session_manager.add_conversation(session_id, "user", result.get("text"))
            
            if not result.get("response"):
                logger.warning("응답이 없습니다. 기본 응답 사용")
                result["response"] = {
                    "message": "주문 처리 중 오류가 발생했습니다. 다시 시도해주세요.",
                    "needs_clarification": False,
                    "clarification_items": [],
                    "is_casual_conversation": False,
                    "order_complete": False,
                    "should_continue_ordering": True,
                    "asking_for_more_items": False
                }
            
            system_response = result["response"]["message"]
            session_manager.add_conversation(session_id, "assistant", system_response)
            logger.info(f"시스템 응답: {system_response}")
            
            if not result["response"].get("is_casual_conversation", False):
                session_manager.resolve_pending_clarification(session_id)
                logger.info("사용자 응답에 따라 첫 번째 명확화 항목 제거")
            else:
                logger.info("일상 대화로 감지되어 명확화 항목 유지")
            
            if result["response"]["needs_clarification"]:
                if result["response"]["clarification_items"]:
                    if result["response"].get("is_casual_conversation", False):
                        logger.info("일상 대화 감지: 기존 명확화 항목 유지")
                    else:
                        new_item = result["response"]["clarification_items"][0]
                        is_duplicate = False
                        for item in session.pending_clarifications:
                            if item.lower() == new_item.lower():
                                is_duplicate = True
                                break
                        
                        if not is_duplicate:
                            session_manager.add_pending_clarification(session_id, new_item)
                            logger.info(f"새 명확화 항목 추가: {new_item}")
            
            if session.pending_clarifications:
                next_item = session.pending_clarifications[0]
                result["response"]["clarification_items"] = [next_item]
                if not result["response"].get("is_casual_conversation", False):
                    result["response"]["message"] = next_item
                result["response"]["needs_clarification"] = True
                logger.info(f"다음 명확화 항목 처리: {next_item}")
            else:
                result["response"]["clarification_items"] = []
                if not result["response"].get("is_casual_conversation", False):
                    result["response"]["message"] = "주문이 완료되었습니다. 감사합니다!"
                result["response"]["needs_clarification"] = False
                logger.info("모든 명확화 항목 처리 완료")
            
            response_data = {
                "status": "success",
                "session_id": session_id,
                "data": {
                    "order": result["analysis"],
                    "message": result["response"]["message"],
                    "needs_clarification": result["response"]["needs_clarification"],
                    "clarification_items": result["response"]["clarification_items"],
                    "is_casual_conversation": result["response"].get("is_casual_conversation", False),
                    "order_complete": False,
                    "should_continue_ordering": True,
                    "asking_for_more_items": False
                }
            }
            
            logger.info(f"명확화 응답 전송: 세션ID={session_id}, 명확화 필요={result['response']['needs_clarification']}")
            return response_data
            
        except Exception as e:
            logger.error(f"명확화 응답 처리 중 오류: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
            
    except Exception as e:
        logger.error(f"명확화 응답 처리 중 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host=host, port=port)
