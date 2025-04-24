import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_training():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logger.info("의도 분류기 훈련 및 테스트를 시작")
        from intent_classifier_training import train_intent_classifier, test_model
        model_path = train_intent_classifier()
        test_model(model_path)
        logger.info(f"의도 분류기 훈련 및 테스트 완료, 모델 저장 경로: {model_path}")
        
    except Exception as e:
        logger.error(f"의도 분류기 훈련 중 오류 발생: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run_training()
