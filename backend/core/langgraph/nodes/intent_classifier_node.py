from typing import Dict, Any
import logging
from ..tools.intent_classifier import IntentClassifier
from ..state import WorkflowState

logger = logging.getLogger("intent_classifier_node")

intent_classifier = None

def get_classifier() -> IntentClassifier:
    global intent_classifier
    if intent_classifier is None:
        logger.info("IntentClassifier 초기화 중...")
        intent_classifier = IntentClassifier()
        logger.info("IntentClassifier 초기화 완료")
    return intent_classifier

def classify_intent(state: Dict[str, Any]) -> Dict[str, Any]:
    new_state = state.copy()
    text = state.get("text", "")
    
    if not text:
        logger.warning("의도 분류를 위한 텍스트가 비었음음")
        new_state["intent_classification"] = {
            "intent": "일상_대화",
            "confidence": 0.0,
            "error": "텍스트가 비어 있습니다"
        }
        return new_state
    
    try:
        classifier = get_classifier()
        logger.info(f"텍스트 의도 분류 중: '{text}'")
        result = classifier.predict(text)
        logger.info(f"분류 결과: 의도={result['intent']}, 신뢰도={result['confidence']:.4f}")
        
        new_state["intent_classification"] = result
        
    except Exception as e:
        logger.error(f"의도 분류 중 오류 발생: {str(e)}")
        new_state["intent_classification"] = {
            "intent": "일상_대화",
            "confidence": 0.0,
            "error": str(e)
        }
    
    return new_state
