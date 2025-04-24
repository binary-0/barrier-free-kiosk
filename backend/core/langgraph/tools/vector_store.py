from typing import Dict, List, Any, Optional
import numpy as np
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger("vector_store")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("sentence-transformers 패키지를 찾을 수 없습니다. 일부 기능이 제한됩니다.")
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    logger.warning("faiss-cpu 패키지를 찾을 수 없습니다. 일부 기능이 제한됩니다.")
    FAISS_AVAILABLE = False

class VectorStore:
    _instance = None
    _initialized = False
    _model = None
    _index = None
    
    def __new__(cls, response_templates_path=None):
        if cls._instance is None:
            cls._instance = super(VectorStore, cls).__new__(cls)
        return cls._instance
        
    def __init__(self, response_templates_path=None):
        if VectorStore._initialized:
            return
            
        self.responses = []

        if VectorStore._model is None and SENTENCE_TRANSFORMERS_AVAILABLE and FAISS_AVAILABLE:
            self._load_model()
            
        if response_templates_path is None:
            response_templates_path = Path(__file__).parent.parent / 'data' / 'response_templates.json'
        
        if os.path.exists(response_templates_path):
            self._load_responses(response_templates_path)
        else:
            logger.warning(f"응답 템플릿 파일을 찾을 수 없습니다: {response_templates_path}")
            
        VectorStore._initialized = True
    
    @classmethod
    def _load_model(cls):
        try:
            logger.info("SentenceTransformer 모델 로드 시작...")
            cls._model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
            logger.info("SentenceTransformer 모델 로드 완료")
        except Exception as e:
            logger.error(f"SentenceTransformer 모델 로드 중 오류 발생: {str(e)}")
            cls._model = None
    
    @property
    def model(self):
        return VectorStore._model
    
    @property    
    def index(self):
        return VectorStore._index
    
    @index.setter
    def index(self, value):
        VectorStore._index = value
            
    def _load_responses(self, templates_path):
        try:
            with open(templates_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                templates = data.get("templates", [])
                
            self.responses = templates
            logger.info(f"응답 템플릿 {len(templates)}개 로드 완료")
            
            if SENTENCE_TRANSFORMERS_AVAILABLE and FAISS_AVAILABLE and self.model:
                texts = [template["text"] for template in templates]
                vectors = self.model.encode(texts)
                
                dimension = vectors.shape[1]
                self.index = faiss.IndexFlatL2(dimension)
                self.index.add(vectors.astype('float32'))
                logger.info("응답 템플릿 벡터화 및 인덱스 생성 완료")
                
        except Exception as e:
            logger.error(f"응답 템플릿 로드 중 오류 발생: {str(e)}")
            self.responses = []
            
    def find_similar_response(self, query: str, response_type: str = None, threshold: float = 0.8) -> Optional[Dict[str, Any]]:
        if not self.responses:
            return None
            
        if SENTENCE_TRANSFORMERS_AVAILABLE and FAISS_AVAILABLE and self.model and self.index:
            try:
                query_vector = self.model.encode([query])[0].astype('float32')
                distances, indices = self.index.search(query_vector.reshape(1, -1), 3)  
                filtered_results = []
                for i, idx in enumerate(indices[0]):
                    if idx < len(self.responses):
                        response = self.responses[idx]
                        if response_type is None or response.get("type") == response_type:
                            score = 1 / (1 + distances[0][i])  
                            if score >= threshold:
                                filtered_results.append((response, score))
                
                if filtered_results:
                    filtered_results.sort(key=lambda x: x[1], reverse=True)
                    response, score = filtered_results[0]
                    logger.info(f"유사 응답 찾음: '{response['text']}' (점수: {score:.4f})")
                    return response
                    
            except Exception as e:
                logger.error(f"벡터 검색 중 오류 발생: {str(e)}")
        
        if response_type:
            type_matches = [r for r in self.responses if r.get("type") == response_type]
            if type_matches:
                import random
                response = random.choice(type_matches)
                logger.info(f"타입 기반 응답 찾음: '{response['text']}'")
                return response
        return None
        
    def get_response_by_type(self, response_type: str) -> Optional[Dict[str, Any]]:
        type_matches = [r for r in self.responses if r.get("type") == response_type]
        if type_matches:
            import random
            return random.choice(type_matches)
        return None
        
    def get_clarification_template(self, menu_name: str, option_type: str) -> str:
        if option_type == "온도":
            response = self.get_response_by_type("temperature_clarification")
            if response:
                template = response["text"]
                return template.replace("아메리카노", menu_name)
            return f"{menu_name}을 따뜻한 음료로 드릴까요, 차가운 음료로 드릴까요?"
        elif option_type == "크기":
            response = self.get_response_by_type("size_clarification")
            if response:
                template = response["text"]
                return template.replace("아메리카노", menu_name)
            return f"{menu_name}을 레귤러 사이즈로 드릴까요, 라지 사이즈로 드릴까요?"
        return ""
