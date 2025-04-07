from typing import Dict, Any
import whisper
import torch
import os
import logging
import time
from pathlib import Path
from ..state import WorkflowState

logger = logging.getLogger("stt_node")

def check_file_exists(file_path: str) -> bool:
    path = Path(file_path)
    if not path.exists():
        logger.error(f"파일이 존재하지 않음: {file_path}")
        return False
    
    if not path.is_file():
        logger.error(f"경로가 파일이 아님: {file_path}")
        return False
    
    if path.stat().st_size == 0:
        logger.error(f"파일 크기가 0: {file_path}")
        return False
    
    return True

# 직접 수정? 일단 small로 해둠 (tiny, base, small, medium, large)
model = None

def load_model():
    global model
    if model is None:
        logger.info("Whisper 모델 로딩 중 (small)...")
        start_time = time.time()
        model = whisper.load_model("medium")
        logger.info(f"Whisper 모델 로딩 완료 ({time.time() - start_time:.2f}초)")
    return model

def process_audio(state: WorkflowState) -> WorkflowState:
    try:
        audio_path = state["audio_path"]
        logger.info(f"STT 처리 시작: {audio_path}")
        
        if not check_file_exists(audio_path):
            state["text"] = "음성 파일을 읽을 수 없습니다."
            return state
        
        file_size = Path(audio_path).stat().st_size
        logger.info(f"오디오 파일 크기: {file_size} bytes")
        
        stt_model = load_model()
        
        start_time = time.time()
        result = stt_model.transcribe(
            audio_path,
            language="ko",
            temperature=0.0,
            task="transcribe",
            fp16=torch.cuda.is_available() # CUDA가 있어야함 -> 현재 4060으로 해둠
        )
        
        processing_time = time.time() - start_time
        
        transcribed_text = result["text"].strip()
        state["text"] = transcribed_text
        
        logger.info(f"STT 처리 완료 ({processing_time:.2f}초): '{transcribed_text}'")
        
        return state
        
    except Exception as e:
        logger.error(f"STT 처리 중 오류 발생: {str(e)}", exc_info=True)
        state["text"] = "음성 인식 중 오류가 발생했습니다."
        return state 