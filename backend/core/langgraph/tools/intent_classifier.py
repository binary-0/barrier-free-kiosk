from typing import Dict, Any, Optional, List, Tuple
import re
import logging
import os
from pathlib import Path
import json
import pickle

logger = logging.getLogger("intent_classifier")

try:
    import numpy as np
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.svm import SVC
    import joblib
    SKLEARN_AVAILABLE = True
except ImportError:
    logger.warning("scikit-learn 패키지를 찾을 수 없습니다. 규칙 기반 분류기만 사용합니다.")
    SKLEARN_AVAILABLE = False

INTENT_CLASSES = {
    "주문": "order",  
    "옵션_선택": "option_selection",  
    "인사": "greeting",  
    "작별": "farewell",  
    "일상_대화": "small_talk",  
    "긍정_응답": "positive_response",  
    "부정_응답": "negative_response",  
    "확인_요청": "confirmation_request"  
}

class IntentClassifier:
    def __init__(self, model_path: Optional[str] = None):
        self.vectorizer = None
        self.classifier = None
        self.intents = ["주문", "옵션_선택", "인사", "작별", "일상_대화"]
        self.rule_patterns = self._load_rule_patterns()
        
        self.rule_confidence_weights = {
            "주문": 0.9,
            "옵션_선택": 0.85,
            "인사": 0.95,
            "작별": 0.95,
            "일상_대화": 0.7
        }
        
        if SKLEARN_AVAILABLE:
            if model_path is None:
                model_path = Path(__file__).parent.parent / 'data' / 'intent_classifier.pkl'
            if os.path.exists(model_path):
                logger.info("ML 기반 의도 분류 모델 로드 완료")
                self._load_model(model_path)
            else:
                logger.info("기존 모델 파일을 찾을 수 없습니다. 규칙 기반 분류기만 사용합니다.")
        
    def _load_rule_patterns(self) -> Dict[str, List[str]]:
        return {
            "인사": [
                r"안녕|하이|헬로|좋은\s*(아침|점심|저녁)",
                r"반가워|만나서\s*반가워",
                r"어떻게\s*지내|잘\s*지내",
                r"반갑습니다",
                r"반갑구나",
                r"어서오세요",
                r"환영합니다",
                r"처음\s*뵙",
                r"오랜만",
                r"방가",
                r"오래간만",
                r"또\s*오셨네요",
                r"어서\s*오십시오",
                r"메뉴\s*무엇",
                r"메뉴\s*뭐",
                r"메뉴\s*어떤",
                r"뭐\s*있어요",
                r"무엇이\s*있나요",
                r"오늘\s*추천\s*메뉴",
                r"추천\s*메뉴\s*뭐",
                r"어떤\s*메뉴\s*있"
            ],
            "작별": [
                r"안녕히\s*가세요|바이|고마워|감사합니다",
                r"잘\s*가|다음에\s*봐",
                r"감사해요",
                r"고맙습니다",
                r"고마워요",
                r"잘\s*먹었습니다",
                r"맛있게\s*먹었",
                r"즐거웠습니다",
                r"수고하세요",
                r"다음에\s*또\s*올게요",
                r"다음에\s*봐요",
                r"좋은\s*하루\s*되세요",
                r"조심히\s*가세요",
                r"즐거운\s*하루\s*되세요",
                r"잘\s*있어요",
                r"다음에\s*또\s*만나요",
                r"다음에\s*또\s*뵙",
                r"다음에\s*또\s*방문",
                r"또\s*올게요",
                r"잘\s*가요",
                r"이만\s*가볼게요",
                r"이만\s*실례",
                r"또\s*뵐게요"
            ],
            "주문": [
                r"(.*?)\s*(\d+)\s*개?\s*주세요",
                r"(.*?)\s*(\d+)\s*개?\s*주문할게",
                r"(.*?)\s*(\d+)\s*개?\s*요청할게",
                r"(.*?)\s*(\d+)\s*개?\s*줘",
                r"(.*?)\s*(\d+)\s*잔\s*(.+)?",
                r"(.*?)\s*한\s*잔\s*(.+)?",
                r"(.*?)\s*하나\s*(.+)?",
                r"(.*?)\s*주세요",
                r"(.*?)\s*주문",
                r"(.*?)\s*[줘|주|주고]",
                r"(.*?)\s*먹고\s*싶어",
                r"(.*?)\s*마시고\s*싶어",
                r"(.*?)\s*주문할게요",
                r"(.*?)\s*주문이요",
                r"(.*?)\s*주문\s*부탁",
                r"(.*?)\s*주문\s*하고\s*싶",
                r"(.*?)\s*마실게요",
                r"(.*?)\s*먹을게요",
                r"(.*?)\s*주문\s*할래요",
                r"(.*?)\s*얼마예요",
                r"(.*?)\s*얼마인가요",
                r"(.*?)\s*얼마에요",
                r"(.*?)\s*가격이\s*어떻게\s*되나요",
                r"(.*?)\s*가격은\s*얼마",
                r"(.*?)\s*줄래요?",
                r"(.*?)\s*주문\s*할게",
                r"(.*?)\s*를?\s*주?문\s*할게",
                r"(.*?)\s*을?\s*주?문\s*할게",
                r"(.*?)\s*로\s*할게요?",
                r"(.*?)\s*로\s*부탁",
                r"(.*?)\s*있나요?",
                r"(.*?)\s*있어요?",
                r"(.*?)\s*는\s*있어요?"
            ],
            "옵션_선택": [
                r"(따뜻하게|핫|아이스|차갑게)",
                r"(레귤러|라지|스몰|보통|크게)",
                r"(디카페인|일반)",
                r"(휘핑크림\s*추가|휘핑크림\s*없이)",
                r"(뜨겁게|차갑게)",
                r"(크게|작게)",
                r"(아이스|핫|따뜻한|차가운)",
                r"(샷\s*추가|샷\s*두\s*번)",
                r"(시럽\s*추가|시럽\s*많이)",
                r"(얼음\s*많이|얼음\s*적게|얼음\s*없이)",
                r"(큰\s*걸로|작은\s*걸로)",
                r"(따뜻한\s*걸로|차가운\s*걸로)",
                r"(라지\s*사이즈|레귤러\s*사이즈)",
                r"(휘핑\s*없이|휘핑\s*많이)",
                r"(시럽\s*적게|시럽\s*빼고)",
                r"(.*?)\s*로\s*주세요",
                r"(.*?)\s*로\s*해주세요",
                r"(.*?)\s*로\s*할게요",
                r"(.*?)\s*로\s*부탁",
                r"(.*?)\s*추가해?주세요",
                r"(.*?)\s*빼주세요",
                r"(.*?)\s*넣어주세요",
                r"(.*?)\s*변경해?주세요",
                r"(.*?)\s*바꿔주세요",
                r"(.*?)\s*선택할?게요?",
                r"(.*?)\s*선택이요"
            ],
            "긍정_응답": [
                r"네",
                r"예",
                r"맞아요",
                r"그래요",
                r"좋아요",
                r"괜찮아요",
                r"알겠습니다",
                r"알겠어요",
                r"그렇게\s*해주세요",
                r"그렇게\s*할게요",
                r"맞습니다",
                r"그게\s*좋겠어요",
                r"동의합니다",
                r"원해요",
                r"할게요",
                r"해주세요"
            ],
            "부정_응답": [
                r"아니요",
                r"아니오",
                r"아뇨",
                r"아닙니다",
                r"아니에요",
                r"다른\s*걸로",
                r"다른\s*걸로\s*할게요",
                r"다른\s*메뉴로",
                r"그건\s*아니",
                r"그렇게\s*안\s*할래요",
                r"싫어요",
                r"별로예요",
                r"안\s*할래요",
                r"안\s*먹을래요",
                r"안\s*마실래요",
                r"괜찮습니다",
                r"그만둘래요"
            ]
        }
        
    def _load_model(self, model_path):
        try:
            with open(model_path, 'rb') as f:
                model_data = pickle.load(f)
                self.vectorizer = model_data['vectorizer']
                self.classifier = model_data['model']
                
                if 'intent_classes' in model_data:
                    self.intents = list(model_data['intent_classes'].keys())
            logger.info("의도 분류 모델 로드 완료")
        except Exception as e:
            logger.error(f"모델 로드 중 오류 발생: {str(e)}")
            self.vectorizer = None
            self.classifier = None
    
    def predict(self, text: str) -> Dict[str, Any]:
        rule_result = self._rule_based_predict(text)
        
        ml_result = None
        if SKLEARN_AVAILABLE and self.vectorizer and self.classifier:
            ml_result = self._ml_based_predict(text)
            
        if ml_result is None:
            return rule_result
            
        if rule_result["confidence"] > 0.8:
            return rule_result
            
        if ml_result["confidence"] > rule_result["confidence"]:
            return ml_result
            
        return rule_result
    
    def _rule_based_predict(self, text: str) -> Dict[str, Any]:
        max_confidence = 0.0
        max_intent = "일상_대화"  
        
        for intent, patterns in self.rule_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    confidence = self.rule_confidence_weights.get(intent, 0.7)
                    match_ratio = len(match.group(0)) / len(text)
                    confidence *= (0.5 + 0.5 * match_ratio)
                    
                    if confidence > max_confidence:
                        max_confidence = confidence
                        max_intent = intent
        
        if max_intent == "주문" or max_intent == "일상_대화":
            from .menu_tools import get_menu_info
            words = re.findall(r'\w+', text)
            for word in words:
                if len(word) >= 2:  
                    menu_info = get_menu_info(word)
                    if menu_info.get("status") == "success":
                        max_intent = "주문"
                        max_confidence = max(max_confidence, 0.85)
                        break
        return {
            "intent": max_intent,
            "confidence": max_confidence
        }
    
    def _ml_based_predict(self, text: str) -> Optional[Dict[str, Any]]:
        if not self.vectorizer or not self.classifier:
            return None
        try:
            X = self.vectorizer.transform([text])
            intent_idx = self.classifier.predict(X)[0]
            probabilities = self.classifier.predict_proba(X)[0]
            max_prob_idx = probabilities.argmax()
            confidence = probabilities[max_prob_idx]
            return {
                "intent": intent_idx,
                "confidence": confidence
            }
        except Exception as e:
            logger.error(f"기계학습 예측 중 오류 발생: {str(e)}")
            return None
