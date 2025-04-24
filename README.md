# 음성인식 기반 대화형 키오스크

음성 인터페이스를 활용하여 사용자 접근성을 높인 AI 기반 카페 키오스크 서비스입니다. 이 프로젝트는 시각 장애인, 노인 등 디지털 기기 사용에 어려움을 겪는 분들도 편리하게 카페 주문을 할 수 있도록 설계되었습니다.

## 주요 구현 내용

- **음성 인식 주문**: 마이크를 통해 자연어로 메뉴를 주문할 수 있습니다.
- **AI 대화 시스템**: 위의 음성 인식 주문은 LangGraph를 기반으로 하여, 규칙 기반 대화 모듈과 GPT-4o LLM을 혼용한 하이브리드 대화형 주문 처리 시스템이 처리합니다.
- **옵션 선택 및 변경**: "아이스 아메리카노 라지 사이즈로 주세요"와 같은 자연스러운 방식으로 메뉴별 옵션을 지정할 수 있습니다.
- **TTS(Text-to-Speech)**: AI 응답을 음성으로 읽어주는 기능을 탑재했습니다.
- **의도 분류 모델**: 규칙 기반과 머신러닝을 결합한 발화 의도 분류 시스템이 주문 처리 앞 단에서 동작합니다.

## 기술 스택

### 백엔드
- **FastAPI**: Python API 프레임워크
- **LangGraph**: 대화형 AI 워크플로우 관리
- **Whisper**: 음성 인식(Speech-To-Text)
- **SQLite**: 메뉴 데이터베이스 구현
- **scikit-learn & sentence-transformers**: 의도 분류 모델 빌드 및 응답 탬플릿의 벡터스토어 구현

### 프론트엔드
- **React**: 사용자 인터페이스
- **Web Speech API**: 브라우저 TTS 기능

## How to run?

### 환경 설정

1. **저장소 클론**
   ```bash
   git clone $link_of_this_repository
   cd barrier-free-kiosk
   ```

2. **백엔드 환경 설정**
   ```bash
   # 가상 환경 생성 및 활성화 (conda 사용 예시)
   conda create -n kiosk python=3.12
   conda activate kiosk
   
   # requirements 패키지 설치
   cd backend
   pip install -r requirements.txt
   ```

3. **OpenAI API 키 설정**
   - 루트 디렉토리에 `.env` 파일을 생성하고 다음과 같이 API 키를 설정합니다:
   ```
   OPENAI_API_KEY=your_api_key
   ```

4. **프론트엔드 환경 설정**
   ```bash
   cd frontend
   npm install
   ```

### 실행

1. **백엔드 서버 실행**
   ```bash
   cd backend
   python api/main.py
   ```
   - 백엔드 서버가 `http://localhost:8000`에서 실행됩니다.

2. **프론트엔드 실행**
   ```bash
   cd frontend
   npm start
   ```
   - 프론트엔드 서버가 `http://localhost:3000`에서 실행됩니다.

3. **의도 분류기 모델 학습 (선택사항)**
   - 발화 의도 분류를 ML 기반 학습된 모델로 진행할지, 규칙 기반 방식으로 진행할지 선택할 수 있습니다. 만약 모델을 새로 학습하고 싶다면 아래 방법을 따라 주세요.
   ```bash
   cd backend/ML
   python run_intent_training.py
   ```
   - 이렇게 하면 의도 분류 모델이 `backend/core/langgraph/data/intent_classifier.pkl`에 저장됩니다. 현재 리포지토리에도 미리 빌드해 둔 .pkl 파일이 업로드 되어있습니다.

## 사용 방법

1. 프론트엔드 접속: 브라우저에서 `http://localhost:3000` 접속
2. 우측 상단 주문 버튼 클릭: 음성 모달이 열립니다.
3. 마이크 버튼 클릭: 주문 내용을 말합니다. ("아이스 아메리카노 한 잔 주세요" 등)
4. AI 응답 확인: AI가 주문을 처리하고 추가 정보가 필요한 경우 질문합니다.
5. 주문 완료: 주문 내역과 총액이 표시됩니다.

## 프로젝트 구조

```
barrier-free-kiosk/
├── backend/               # 백엔드 폴더
│   ├── api/               # FastAPI endpoint 구현
│   ├── core/              # 핵심 대화 로직 구현
│   │   ├── langgraph/     # LangGraph 워크플로우
│   │   │   ├── data/      # 의도 분류기 모델 등의 데이터
│   │   │   ├── nodes/     # LangGraph 노드
│   │   │   └── tools/     # LLM Tool 저장
│   │   └── models/        # 데이터 모델
│   ├── ML/                # 의도 분류기 학습 코드
│   └── requirements.txt   # requirements 패키지 모음
│
└── frontend/              # 프론트엔드 폴더
    ├── public/            # 정적 파일
    └── src/               # React 소스 코드
        ├── components/    # 컴포넌트
        ├── hooks/         # 커스텀 hook
        └── services/      # API 서비스
```

## 주의사항

- 음성 인식을 위해 마이크 접근 권한이 필요합니다.
- Whisper 모델은 초기 실행 시 다운로드될 수 있으므로 인터넷 연결이 필요합니다.
- TTS 기능은 브라우저 호환성에 따라 다를 수 있습니다.


MIT License