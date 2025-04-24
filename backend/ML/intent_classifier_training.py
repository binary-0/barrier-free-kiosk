


import os
import re
import pickle
import logging
import random
import numpy as np
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import classification_report, accuracy_score


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

INTENT_CLASSES = {
    "주문": "order",  
    "옵션_선택": "option_selection",  
    "인사": "greeting",  
    "작별": "farewell",  
    "일상_대화": "small_talk"  
}

TRAINING_DATA = [
    {"text": "아메리카노 주세요", "intent": "주문"},
    {"text": "카페라떼 한잔 주문할게요", "intent": "주문"},
    {"text": "에스프레소 하나 주세요", "intent": "주문"},
    {"text": "카페모카 주문이요", "intent": "주문"},
    {"text": "바닐라라떼 두잔 주세요", "intent": "주문"},
    {"text": "아이스티 한잔 주문할게요", "intent": "주문"},
    {"text": "아이스 아메리카노 하나요", "intent": "주문"},
    {"text": "핫초코 주세요", "intent": "주문"},
    {"text": "녹차라떼 하나 주문이요", "intent": "주문"},
    {"text": "딸기 스무디 주세요", "intent": "주문"},
    {"text": "카라멜 마끼아또 한잔이요", "intent": "주문"},
    {"text": "아메리카노 두잔 주세요", "intent": "주문"},
    {"text": "카페라떼 마실게요", "intent": "주문"},
    {"text": "아이스 초코 주문할게요", "intent": "주문"},
    {"text": "아메리카노 한잔이랑 카페라떼 한잔 주세요", "intent": "주문"},
    {"text": "카페모카 하나 주문할게요", "intent": "주문"},
    {"text": "바닐라라떼 주세요", "intent": "주문"},
    {"text": "아메리카노 세잔 주문이요", "intent": "주문"},
    {"text": "아이스 바닐라라떼 주세요", "intent": "주문"},
    {"text": "녹차라떼 두잔 주문할게요", "intent": "주문"},
    {"text": "아메리카노로 할게요", "intent": "주문"},
    {"text": "카페라떼로 부탁합니다", "intent": "주문"},
    {"text": "아이스 아메리카노 얼음 많이 주세요", "intent": "주문"},
    {"text": "따뜻한 카페라떼 한잔이요", "intent": "주문"},
    {"text": "바닐라라떼 샷 추가해서 주세요", "intent": "주문"},
    {"text": "아메리카노 디카페인으로 주문할게요", "intent": "주문"},
    {"text": "차가운 녹차라떼 큰 사이즈로 주세요", "intent": "주문"},
    {"text": "핫초코 휘핑크림 많이 주세요", "intent": "주문"},
    {"text": "아이스 티 레몬 추가해서 주문할게요", "intent": "주문"},
    {"text": "아메리카노 하나랑 카페라떼 하나 주문이요", "intent": "주문"},

    {"text": "아이스로 주세요", "intent": "옵션_선택"},
    {"text": "핫으로 해주세요", "intent": "옵션_선택"},
    {"text": "따뜻하게 주세요", "intent": "옵션_선택"},
    {"text": "차갑게 해주세요", "intent": "옵션_선택"},
    {"text": "휘핑크림 추가해주세요", "intent": "옵션_선택"},
    {"text": "휘핑크림 빼주세요", "intent": "옵션_선택"},
    {"text": "라지 사이즈로 주세요", "intent": "옵션_선택"},
    {"text": "레귤러로 해주세요", "intent": "옵션_선택"},
    {"text": "큰 사이즈로 주세요", "intent": "옵션_선택"},
    {"text": "작은 사이즈로 해주세요", "intent": "옵션_선택"},
    {"text": "디카페인으로 주세요", "intent": "옵션_선택"},
    {"text": "일반 원두로 해주세요", "intent": "옵션_선택"},
    {"text": "시럽 추가해 주세요", "intent": "옵션_선택"},
    {"text": "시럽 빼고 주세요", "intent": "옵션_선택"},
    {"text": "얼음 많이 넣어주세요", "intent": "옵션_선택"},
    {"text": "얼음 적게 해주세요", "intent": "옵션_선택"},
    {"text": "샷 추가해주세요", "intent": "옵션_선택"},
    {"text": "바닐라 시럽 추가요", "intent": "옵션_선택"},
    {"text": "카라멜 시럽 넣어주세요", "intent": "옵션_선택"},
    {"text": "헤이즐넛 시럽으로 해주세요", "intent": "옵션_선택"},
    {"text": "큰 걸로 주세요", "intent": "옵션_선택"},
    {"text": "작은 걸로 할게요", "intent": "옵션_선택"},
    {"text": "따뜻한 걸로 부탁드려요", "intent": "옵션_선택"},
    {"text": "차가운 걸로 해주세요", "intent": "옵션_선택"},
    {"text": "휘핑크림 많이 넣어주세요", "intent": "옵션_선택"},
    {"text": "얼음은 조금만 넣어주세요", "intent": "옵션_선택"},
    {"text": "샷 두 번 추가해주세요", "intent": "옵션_선택"},
    {"text": "시럽은 적게 넣어주세요", "intent": "옵션_선택"},
    {"text": "라지 사이즈로 변경해주세요", "intent": "옵션_선택"},
    {"text": "디카페인으로 변경할게요", "intent": "옵션_선택"},

    {"text": "안녕하세요", "intent": "인사"},
    {"text": "안녕", "intent": "인사"},
    {"text": "반갑습니다", "intent": "인사"},
    {"text": "좋은 아침이에요", "intent": "인사"},
    {"text": "점심 식사 하셨나요", "intent": "인사"},
    {"text": "저녁 식사는 하셨어요?", "intent": "인사"},
    {"text": "처음 뵙겠습니다", "intent": "인사"},
    {"text": "잘 지내셨어요?", "intent": "인사"},
    {"text": "방가방가", "intent": "인사"},
    {"text": "오랜만이에요", "intent": "인사"},
    {"text": "어서오세요", "intent": "인사"},
    {"text": "안녕하십니까", "intent": "인사"},
    {"text": "반가워요", "intent": "인사"},
    {"text": "환영합니다", "intent": "인사"},
    {"text": "오늘 날씨 좋네요", "intent": "인사"},
    {"text": "좋은 하루 되고 계신가요?", "intent": "인사"},
    {"text": "잘 지내셨어요?", "intent": "인사"},
    {"text": "오래간만이네요", "intent": "인사"},
    {"text": "어서 오십시오", "intent": "인사"},
    {"text": "만나서 반갑습니다", "intent": "인사"},
    {"text": "요즘 어떻게 지내세요?", "intent": "인사"},
    {"text": "오랜만에 뵙네요", "intent": "인사"},
    {"text": "반갑구나", "intent": "인사"},
    {"text": "메뉴가 무엇이 있나요?", "intent": "인사"},
    {"text": "오늘의 추천 메뉴는 뭔가요?", "intent": "인사"},

    {"text": "안녕히 계세요", "intent": "작별"},
    {"text": "안녕히 가세요", "intent": "작별"},
    {"text": "감사합니다", "intent": "작별"},
    {"text": "고맙습니다", "intent": "작별"},
    {"text": "다음에 또 올게요", "intent": "작별"},
    {"text": "잘 있어요", "intent": "작별"},
    {"text": "다음에 봐요", "intent": "작별"},
    {"text": "좋은 하루 되세요", "intent": "작별"},
    {"text": "즐거운 시간 보내세요", "intent": "작별"},
    {"text": "조심히 가세요", "intent": "작별"},
    {"text": "다음에 또 뵙겠습니다", "intent": "작별"},
    {"text": "감사했습니다", "intent": "작별"},
    {"text": "잘 가요", "intent": "작별"},
    {"text": "이만 가볼게요", "intent": "작별"},
    {"text": "고마워요", "intent": "작별"},
    {"text": "잘 먹었습니다", "intent": "작별"},
    {"text": "맛있게 먹었어요", "intent": "작별"},
    {"text": "즐거웠습니다", "intent": "작별"},
    {"text": "이만 실례하겠습니다", "intent": "작별"},
    {"text": "다음에 또 방문할게요", "intent": "작별"},
    {"text": "즐거운 하루 되세요", "intent": "작별"},
    {"text": "수고하세요", "intent": "작별"},
    {"text": "좋은 하루 마무리하세요", "intent": "작별"},
    {"text": "다음에 또 만나요", "intent": "작별"},
    {"text": "잘 가세요", "intent": "작별"},

    {"text": "날씨가 좋네요", "intent": "일상_대화"},
    {"text": "오늘 바쁘신가요?", "intent": "일상_대화"},
    {"text": "이 카페는 언제부터 운영했나요?", "intent": "일상_대화"},
    {"text": "여기 단골인데요", "intent": "일상_대화"},
    {"text": "처음 왔어요", "intent": "일상_대화"},
    {"text": "추천 메뉴가 뭐예요?", "intent": "일상_대화"},
    {"text": "화장실은 어디에 있나요?", "intent": "일상_대화"},
    {"text": "와이파이 비밀번호 알 수 있을까요?", "intent": "일상_대화"},
    {"text": "여기 자주 오시나요?", "intent": "일상_대화"},
    {"text": "이 근처에 주차장이 있나요?", "intent": "일상_대화"},
    {"text": "몇 시까지 영업하나요?", "intent": "일상_대화"},
    {"text": "여기 케이크도 맛있나요?", "intent": "일상_대화"},
    {"text": "이 동네에 사세요?", "intent": "일상_대화"},
    {"text": "이 카페 분위기가 좋네요", "intent": "일상_대화"},
    {"text": "요새 장사가 잘 되나요?", "intent": "일상_대화"},
    {"text": "이 메뉴가 인기가 많나요?", "intent": "일상_대화"},
    {"text": "요새 사람들이 많이 오나요?", "intent": "일상_대화"},
    {"text": "휴무일은 언제인가요?", "intent": "일상_대화"},
    {"text": "테이크아웃도 가능한가요?", "intent": "일상_대화"},
    {"text": "포장도 되나요?", "intent": "일상_대화"},
    {"text": "음료는 어디서 받나요?", "intent": "일상_대화"},
    {"text": "주문은 어디서 하나요?", "intent": "일상_대화"},
    {"text": "여기 앉아도 되나요?", "intent": "일상_대화"},
    {"text": "콘센트 있는 자리 있나요?", "intent": "일상_대화"},
    {"text": "오늘 특별한 메뉴가 있나요?", "intent": "일상_대화"}
]

ORDER_TEMPLATES = [
    "{}",
    "{} 주세요",
    "{} 주문할게요",
    "{} 하나 주세요",
    "{} 두잔 주세요",
    "{} 한잔 주문이요",
    "{} 마실게요",
    "{} 주문이요",
    "{} 세잔 주세요",
    "{} 두개 주문할게요",
    "{} 한잔 부탁합니다",
    "{} 한 개 주문할게요",
    "{} 먹고 싶어요",
    "{} 마시고 싶어요",
    "{} 주문하려고 해요",
    "{} 있나요?",
    "{}는 있어요?",
    "{} 한잔 먹을게요",
    "{}로 할게요",
    "{}로 부탁합니다"
]

OPTION_TEMPLATES = [
    "{}로 주세요",
    "{}로 해주세요",
    "{} 주세요",
    "{} 해주세요",
    "{} 부탁드려요",
    "{} 선택할게요",
    "{} 추가해주세요",
    "{} 빼주세요",
    "{} 넣어주세요",
    "{} 원해요",
    "{} 걸로 주세요",
    "{} 걸로 할게요",
    "{} 걸로 부탁해요",
    "{} 옵션으로 해주세요",
    "{} 선택이요",
    "{} 변경해주세요",
    "{} 바꿔주세요",
    "{} 없이 해주세요",
    "{} 많이 넣어주세요",
    "{} 적게 넣어주세요"
]

MENU_ITEMS = [
    "아메리카노", "카페라떼", "카푸치노", "바닐라라떼", "카페모카", 
    "에스프레소", "아이스티", "핫초코", "녹차라떼", "딸기 스무디", 
    "카라멜 마끼아또", "화이트 초콜릿 모카", "헤이즐넛 라떼", "콜드브루", 
    "밀크티", "레몬에이드", "자몽에이드", "청포도 에이드"
]

OPTIONS = [
    "아이스", "핫", "따뜻하게", "차갑게", "휘핑크림 추가", "휘핑크림 빼고", 
    "라지", "레귤러", "큰 사이즈", "작은 사이즈", "디카페인", "일반 원두", 
    "시럽 추가", "시럽 빼고", "얼음 많이", "얼음 적게", "샷 추가",
    "따뜻한 것", "차가운 것", "큰 것", "작은 것", "휘핑크림 많이", 
    "휘핑 없이", "얼음 없이", "샷 두 번", "시럽 많이"
]

def generate_additional_data():
    additional_data = []
    for menu in MENU_ITEMS:
        for template in ORDER_TEMPLATES:
            text = template.format(menu)
            additional_data.append({"text": text, "intent": "주문"})
    
    for option in OPTIONS:
        for template in OPTION_TEMPLATES:
            text = template.format(option)
            additional_data.append({"text": text, "intent": "옵션_선택"})
    
    unique_texts = set()
    unique_data = []
    for item in additional_data:
        if item["text"] not in unique_texts:
            unique_texts.add(item["text"])
            unique_data.append(item)
    
    sampled_data = []
    intent_counts = {"주문": 0, "옵션_선택": 0}
    random.shuffle(unique_data)
    for item in unique_data:
        intent = item["intent"]
        if intent_counts.get(intent, 0) < 100:
            sampled_data.append(item)
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
    return sampled_data

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'[^\w\s?!.,가-힣]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def train_intent_classifier():
    all_data = TRAINING_DATA + generate_additional_data()
    random.shuffle(all_data)
    texts = [preprocess_text(item["text"]) for item in all_data]
    intents = [item["intent"] for item in all_data]
    
    X_train, X_test, y_train, y_test = train_test_split(
        texts, intents, test_size=0.2, random_state=42, stratify=intents
    )
    
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=5000,
        min_df=2,
        max_df=0.8
    )
    
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    param_grid = {
        'C': [0.1, 1, 10, 100],
        'gamma': ['scale', 'auto'],
        'kernel': ['linear', 'rbf']
    }
    
    grid_search = GridSearchCV(
        SVC(probability=True),
        param_grid,
        cv=5,
        scoring='accuracy',
        verbose=1
    )
    
    logger.info("그리드 서치를 통한 최적 하이퍼파라미터 탐색 중...")
    grid_search.fit(X_train_vec, y_train)
    
    best_model = grid_search.best_estimator_
    logger.info(f"최적 하이퍼파라미터: {grid_search.best_params_}")
    
    y_pred = best_model.predict(X_test_vec)
    accuracy = accuracy_score(y_test, y_pred)
    logger.info(f"테스트 정확도: {accuracy:.4f}")
    logger.info("\n분류 보고서:")
    report = classification_report(y_test, y_pred)
    logger.info(f"\n{report}")
    
    base_dir = Path(__file__).resolve().parent.parent
    model_dir = base_dir / "core" / "langgraph" / "data"
    model_dir.mkdir(parents=True, exist_ok=True)
    model_path = model_dir / "intent_classifier.pkl"
    
    with open(model_path, 'wb') as f:
        pickle.dump({
            'vectorizer': vectorizer,
            'model': best_model,
            'intent_classes': INTENT_CLASSES
        }, f)
    
    logger.info(f"의도 분류기를를 {str(model_path)}에 저장함")
    return str(model_path)

def test_model(model_path):
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    vectorizer = model_data['vectorizer']
    model = model_data['model']
    intent_classes = model_data['intent_classes']
    
    test_sentences = [
        "아메리카노 주세요",
        "아이스로 해주세요",
        "안녕하세요",
        "감사합니다",
        "이 카페는 언제부터 했나요?",
        "바닐라라떼 두잔 주문할게요",
        "휘핑크림 추가해주세요",
        "디카페인으로 해주세요",
        "좋은 하루 되세요",
        "여기 화장실이 어디에요?"
    ]
    
    logger.info("\n----- 테스트 문장 의도 분류 결과 -----")
    for sentence in test_sentences:
        preprocessed = preprocess_text(sentence)
        vector = vectorizer.transform([preprocessed])
        intent_idx = model.predict(vector)[0]
        proba = np.max(model.predict_proba(vector))
        
        logger.info(f"문장: '{sentence}'")
        logger.info(f"분류된 의도: '{intent_idx}' (확률: {proba:.4f})")
        logger.info("-" * 40)

if __name__ == "__main__":
    model_path = train_intent_classifier()
    test_model(model_path)
