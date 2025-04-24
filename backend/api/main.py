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
from core.langgraph.tools.vector_store import VectorStore

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


UPLOAD_DIR = Path("temp_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def cleanup_old_files():
    try:
        current_time = time.time()
        for file_path in UPLOAD_DIR.glob('*.webm'):
            file_age = current_time - file_path.stat().st_mtime
            if file_age > 3600:  
                file_path.unlink()
                logger.info(f"오래된 임시 파일 삭제: {file_path}")
    except Exception as e:
        logger.error(f"임시 파일 정리 중 오류: {str(e)}")

@app.on_event("startup")
async def startup_event():
    
    logger.info("Whisper STT 모델 로드 시작...")
    load_model()
    logger.info("Whisper STT 모델 로드 완료")
    
    
    logger.info("SentenceTransformer 모델 초기화 시작...")
    vector_store = VectorStore()  
    logger.info("SentenceTransformer 모델 초기화 완료")
    
    cleanup_old_files()

    init_db()
    populate_db()
    logger.info("DB 초기화 완료")
    
    global session_manager
    session_manager = OrderSessionManager()
    
    removed_sessions = session_manager.cleanup_old_sessions(max_age_minutes=60)
    logger.info(f"오래된 세션 정리: {removed_sessions}개 세션 제거됨")
    
    global order_analysis_chain
    order_analysis_chain = create_order_analysis_workflow()
    logger.info("LangGraph 워크플로우 초기화 완료")


session_manager = None
order_analysis_chain = None


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
        
        logger.info("LangGraph 워크플로우 실행 시작")
        try:
            result = order_analysis_chain.invoke(initial_state)
            if not result:
                logger.error("LangGraph 워크플로우가 None 반환")
                raise ValueError("워크플로우 실행 결과가 없음")
                
            logger.info(f"LangGraph 워크플로우 실행 완료: 인식된 텍스트={result.get('text', '')}")
            
            try:
                temp_file_path.unlink()
                logger.info(f"임시 파일 삭제 완료: {temp_file_path}")
            except Exception as e:
                logger.warning(f"임시 파일 삭제 실패: {str(e)}")
            
            
            if not result.get("analysis"):
                logger.warning("분석 결과 X, 기본값 사용")
                result["analysis"] = {
                    "items": [],
                    "total_price": 0,
                    "special_requests": ""
                }
            
            if result["response"].get("is_casual_conversation", False) and session.current_order:
                logger.info(f"일상 대화 감지: 기존 주문 정보 유지 (세션 ID: {session_id})")
                result["analysis"] = session.current_order
            
            session_manager.update_session(session_id, result["analysis"])
            logger.info(f"세션 업데이트 완료 (세션 ID: {session_id})")
            
            if not result.get("response"):
                logger.warning("응답 X, 기본 응답 사용")
                result["response"] = {
                    "message": "주문 처리 중 오류가 발생했습니다. 다시 시도해주세요.",
                    "needs_clarification": False,
                    "clarification_items": []
                }
                
            system_response = result["response"]["message"]
            session_manager.add_conversation(session_id, "assistant", system_response)
            logger.info(f"시스템 응답: {system_response}")
             
            if result["response"]["needs_clarification"]:
                if result.get("pending_clarifications_resolved", False):
                    logger.info("규칙 기반 노드에서 명확화 항목이 해결된 것으로 감지")
                    
                    session_manager.clear_pending_clarifications(session_id)
                    
                    if result["response"]["clarification_items"]:
                        first_item = result["response"]["clarification_items"][0]
                        session_manager.add_pending_clarification(session_id, first_item)
                        logger.info(f"새 명확화 항목 추가: {first_item}")
                        result["response"]["clarification_items"] = [first_item]
                else:
                    session_manager.clear_pending_clarifications(session_id)
                    if result["response"]["clarification_items"]:
                        first_item = result["response"]["clarification_items"][0]
                        session_manager.add_pending_clarification(session_id, first_item)
                        logger.info(f"명확화 항목 추가: {first_item}")
                        
                        result["response"]["clarification_items"] = [first_item]
            else:
                session_manager.clear_pending_clarifications(session_id)
            
            if result["response"]["needs_clarification"] and result["response"]["clarification_items"]:
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
            logger.info("처리할 명확화 항목이 없지만 워크플로우를 계속 실행")
        
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
                logger.error("LangGraph 워크플로우가 None 반환")
                raise ValueError("워크플로우 실행 결과가 없습니다.")
                
            logger.info(f"LangGraph 워크플로우 실행 완료: 인식된 텍스트={result.get('text', '')}")
            
            try:
                temp_file_path.unlink()
                logger.info(f"임시 파일 삭제 완료: {temp_file_path}")
            except Exception as e:
                logger.warning(f"임시 파일 삭제 실패: {str(e)}")
            
            if not result.get("analysis"):
                logger.warning("분석 결과 X, 기존 주문 정보 유지")
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
                logger.warning("응답 X, 기본 응답 사용")
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
            
            if result.get("pending_clarifications_resolved", False):
                logger.info("규칙 기반 노드에서 명확화 항목이 해결된 것으로 감지")
                
                if session.pending_clarifications:
                    session_manager.resolve_pending_clarification(session_id)
                    logger.info("명확화 항목 해결 처리 완료")
            elif not result["response"].get("is_casual_conversation", False):
                
                if session.pending_clarifications:
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
            
            has_pending_clarifications = len(session.pending_clarifications) > 0
            
            if has_pending_clarifications:
                next_item = session.pending_clarifications[0]
                result["response"]["clarification_items"] = [next_item]
                if not result["response"].get("is_casual_conversation", False):
                    result["response"]["message"] = next_item
                result["response"]["needs_clarification"] = True
                logger.info(f"다음 명확화 항목 처리: {next_item}")
            else:
                if result["response"].get("clarification_items") and not result["response"].get("is_casual_conversation", False):
                    
                    new_clarification = result["response"]["clarification_items"][0]
                    session_manager.add_pending_clarification(session_id, new_clarification)
                    result["response"]["needs_clarification"] = True
                    result["response"]["message"] = new_clarification  
                    logger.info(f"새 명확화 항목 추가됨 (세션에 없었음): {new_clarification}")
                else:
                    result["response"]["clarification_items"] = []
                    if not result["response"].get("is_casual_conversation", False):
                        
                        if result["response"].get("asking_for_more_items", False):
                            result["response"]["message"] = "더 주문하실 것이 있으신가요?"
                            result["response"]["clarification_items"] = ["더 주문하실 것이 있으신가요?"]
                            result["response"]["needs_clarification"] = True
                            
                            session_manager.add_pending_clarification(session_id, "더 주문하실 것이 있으신가요?")
                        else:
                            
                            result["response"]["message"] = "주문이 완료되었습니다. 감사합니다!"
                            result["response"]["needs_clarification"] = False
                    else:
                        
                        result["response"]["needs_clarification"] = False
                    
                    logger.info("모든 명확화 항목 처리 완료")
            
            
            has_pending_clarifications_after_update = len(session.pending_clarifications) > 0
            if has_pending_clarifications_after_update:
                result["response"]["needs_clarification"] = True
                if len(result["response"]["clarification_items"]) == 0:
                    result["response"]["clarification_items"] = [session.pending_clarifications[0]]
                    
                    if not result["response"].get("is_casual_conversation", False):
                        result["response"]["message"] = session.pending_clarifications[0]
                logger.info(f"응답 전 최종 확인: 명확화 항목 있음 ({session.pending_clarifications[0]})")
            
            response_data = {
                "status": "success",
                "session_id": session_id,
                "data": {
                    "order": result["analysis"],
                    "message": result["response"]["message"],
                    "needs_clarification": result["response"]["needs_clarification"],
                    "clarification_items": result["response"]["clarification_items"],
                    "is_casual_conversation": result["response"].get("is_casual_conversation", False),
                    "order_complete": result["response"].get("order_complete", False),
                    "should_continue_ordering": True,
                    "asking_for_more_items": result["response"].get("asking_for_more_items", False)
                }
            }
            
            logger.info(f"명확화 응답 전송: 세션ID={session_id}, 명확화 필요={result['response']['needs_clarification']}, 명확화 항목={result['response']['clarification_items']}")
            return response_data
            
        except Exception as e:
            logger.error(f"명확화 응답 처리 중 오류: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
            
    except Exception as e:
        logger.error(f"명확화 응답 처리 중 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/cleanup-sessions")
async def cleanup_sessions(max_age_minutes: int = 30):
    try:
        removed_count = session_manager.cleanup_old_sessions(max_age_minutes)
        cleanup_old_files()  
        
        return {
            "status": "success",
            "message": f"{removed_count}개의 오래된 세션이 제거되었습니다."
        }
    except Exception as e:
        logger.error(f"세션 정리 중 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/sessions")
async def get_sessions():
    try:
        sessions_info = session_manager.get_all_sessions_info()
        return {
            "status": "success",
            "data": {
                "sessions_count": len(sessions_info),
                "sessions": sessions_info
            }
        }
    except Exception as e:
        logger.error(f"세션 정보 조회 중 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host=host, port=port)
