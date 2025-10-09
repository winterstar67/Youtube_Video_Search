# YouTube Search & Storage Web Application

FastAPI 기반 웹 애플리케이션으로 YouTube 영상 자막 검색 및 저장 기능을 제공합니다.

## 기능

### 1. 검색 기능 (`/search`)
- 사용자 쿼리를 입력받아 VectorDB에서 의미론적 검색 수행
- Pinecone index와 namespace 지정 가능
- Reranking 옵션으로 더 정확한 검색 결과 제공
- 검색 결과를 JSON 파일로 자동 저장

### 2. 저장 기능 (`/store`)
- YouTube 영상 URL을 입력받아 자동 처리
- Author, Comment 메타데이터 추가 가능
- 자동 파이프라인 실행:
  1. YouTube 자막 추출 (`Youtube_transcription.py`)
  2. 자막 전처리 및 문장 분할 (`transcript_processing.py`)
  3. VectorDB에 저장 (`Store_on_VectorDB.py`)

## 설치 및 실행

### 1. 의존성 설치
```bash
cd app
pip install -r requirements.txt
```

### 2. 환경 변수 설정
프로젝트 루트의 `.env` 파일에 다음 환경 변수가 설정되어 있어야 합니다:
```
PINECONE_API_KEY=your_api_key
PINECONE_HOST=your_host
YOUTUBE_API_KEY=your_api_key
```

### 3. 애플리케이션 실행
```bash
# 개발 모드
python main.py

# 또는 uvicorn으로 직접 실행
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 브라우저에서 접속
```
http://localhost:8000
```

## API 엔드포인트

### GET `/`
홈 페이지

### GET `/search`
검색 페이지

### POST `/search/execute`
검색 실행
- Parameters:
  - `query` (str): 검색 쿼리
  - `index_name` (str): Pinecone index 이름 (기본값: "developer-quickstart-py")
  - `namespace` (str): Pinecone namespace (기본값: "test")
  - `rerank` (bool): Reranking 사용 여부 (기본값: true)

### GET `/store`
저장 페이지

### POST `/store/execute`
영상 저장 실행
- Parameters:
  - `video_url` (str): YouTube 영상 URL
  - `author` (str, optional): 작성자/출처
  - `comment` (str, optional): 코멘트

### GET `/health`
Health check 엔드포인트

## 디렉토리 구조

```
app/
├── main.py              # FastAPI 애플리케이션 메인 파일
├── requirements.txt     # Python 의존성
├── README.md           # 이 파일
├── templates/          # HTML 템플릿
│   ├── home.html       # 홈 페이지
│   ├── search.html     # 검색 페이지
│   └── store.html      # 저장 페이지
└── static/             # 정적 파일 (CSS, JS, 이미지 등)
```

## 주의사항

1. 영상 저장 처리는 영상 길이에 따라 몇 분이 걸릴 수 있습니다.
2. Pinecone API 사용량에 주의하세요.
3. YouTube API quota 제한에 주의하세요.

## 문제 해결

### 포트가 이미 사용 중인 경우
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### CORS 오류 발생 시
`main.py`에 CORS 미들웨어를 추가:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
