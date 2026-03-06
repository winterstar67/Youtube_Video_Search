# YouTube Semantic Search

유튜브 영상의 자막을 Vector DB에 저장하고, 자연어 쿼리로 원하는 발언의 타임스탬프를 찾아주는 시맨틱 검색 시스템입니다.

## 프로젝트 개요

유튜브 영상에서 특정 내용이 언급된 시점을 찾으려면, 영상을 되감으며 직접 탐색해야 하는 비효율이 발생합니다. 이 프로젝트는 해당 문제를 해결하기 위해 자막 텍스트를 Vector DB(Pinecone)에 저장하고, 자연어 쿼리만으로 원하는 장면의 타임스탬프를 즉시 반환하는 RAG 파이프라인을 구축합니다.

**주요 기능**

- YouTube 영상 자막 및 메타데이터 자동 수집
- SaT(Segment any Text) 기반 문장 단위 분리 및 슬라이딩 윈도우 적용
- 각 문장 chunk에 시작/종료 타임스탬프(HH:MM:SS) 자동 부착
- Pinecone Vector DB에 임베딩 저장
- 자연어 쿼리로 관련 장면 타임스탬프 검색

## 파이프라인 구조

```
1. 자막 수집            Youtube_transcription.py
        |
        v
2. (선택) 오타 교정     gpt_based_weired_word_sensor.py
        |
        v
3. 문장 분리 & 변환     transcript_processing.py
        |                  - SaT 문장 분리
        |                  - 슬라이딩 윈도우 적용
        |                  - 타임스탬프 추출
        v
4. Vector DB 저장       Store_on_VectorDB.py
        |                  - Pinecone 배치 업서트
        v
5. 시맨틱 검색          Semantic_search.py (또는 Pinecone 웹 콘솔)
```

## 입력 데이터 준비

파이프라인을 실행하기 전에 `data/raw_data/` 폴더 아래 다음 파일들을 준비해 주세요.

---

### (1) `data/raw_data/video_link_target.yaml`

수집할 YouTube 영상 목록과 저장할 Pinecone 인덱스 설정을 지정합니다.

```yaml
https://www.youtube.com/watch?v=VIDEO_ID:
  index_name: developer-quickstart-py
  namespace: Video_RAG
  cloud: aws
  region: us-east-1
  embed:
    model: llama-text-embed-v2
    field_map:
      text: chunk_text
  Author: ""
  Comment: ""
```

| 키 | 설명 |
|---|---|
| (최상위 키) | YouTube 영상 URL |
| `index_name` | Pinecone 인덱스 이름 |
| `namespace` | Pinecone 네임스페이스 |
| `cloud` / `region` | Pinecone 인덱스가 배포된 클라우드 및 리전 |
| `embed.model` | 사용할 임베딩 모델명 |
| `embed.field_map.text` | 임베딩 대상 필드 이름 (`chunk_text` 고정) |
| `Author` | 영상 제작자 (선택, 메타데이터 용도) |
| `Comment` | 메모 (선택) |

여러 영상을 처리하려면 URL을 새 키로 추가하면 됩니다.

```yaml
https://www.youtube.com/watch?v=VIDEO_ID_1:
  index_name: my-index
  namespace: Video_RAG
  cloud: aws
  region: us-east-1
  embed:
    model: llama-text-embed-v2
    field_map:
      text: chunk_text
  Author: ""
  Comment: ""

https://www.youtube.com/watch?v=VIDEO_ID_2:
  index_name: my-index
  namespace: Video_RAG
  cloud: aws
  region: us-east-1
  embed:
    model: llama-text-embed-v2
    field_map:
      text: chunk_text
  Author: ""
  Comment: ""
```

---

### (2) `data/raw_data/transcript_processing_config.json`

SaT 문장 분리 모델의 동작 파라미터를 설정합니다.

```json
{
  "SaT_model": "sat-1l-sm",
  "SaT_threshold": 0.5,
  "concat_length": 3,
  "use_gpu": "False"
}
```

| 키 | 설명 |
|---|---|
| `SaT_model` | 사용할 SaT 모델명 (예: `sat-1l-sm`, `sat-3l`) |
| `SaT_threshold` | 문장 경계 감지 임계값 (0~1, 높을수록 경계를 적게 검출) |
| `concat_length` | 슬라이딩 윈도우 chunk 크기 (인접 문장 몇 개를 묶을지) |
| `use_gpu` | GPU 사용 여부 (`"True"` / `"False"`) |

---

### (3) `data/raw_data/query.json` (선택)

`Semantic_search.py`를 직접 실행할 때 사용하는 검색 쿼리입니다. Pinecone 웹 콘솔을 사용하는 경우에는 필요하지 않습니다.

```json
{
  "inputs": {"text": "원하는 내용을 자연어로 입력하세요"},
  "top_k": 5
}
```

| 키 | 설명 |
|---|---|
| `inputs.text` | 검색할 자연어 쿼리 |
| `top_k` | 반환할 상위 결과 개수 |

---

## 환경 설정

### 1) 가상 환경 생성 및 패키지 설치

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 아래 변수를 설정해 주세요.

```env
YOUTUBE_API_KEY=
PINECONE_API_KEY=
PINECONE_HOST=
OPENAI_API_KEY=
```

| 변수 | 설명 | 필수 여부 |
|---|---|---|
| `YOUTUBE_API_KEY` | YouTube Data API v3 키 | 필수 |
| `PINECONE_API_KEY` | Pinecone API 키 | 필수 |
| `PINECONE_HOST` | Pinecone 인덱스 호스트 URL | 필수 |
| `OPENAI_API_KEY` | GPT 기반 오타 교정 사용 시 필요 | 선택 |

`.env` 파일 및 API 키는 절대 Git에 커밋하지 마세요.

---

## 실행 방법

아래 순서대로 단계별로 실행해 주세요.

### 1단계 — 자막 수집

```bash
python src/Youtube_transcription.py
```

`video_link_target.yaml`에 등록된 YouTube 영상의 자막과 메타데이터(제목, 영상 ID 등)를 수집합니다. 수집 결과는 `data/results/Youtube_transcription/` 폴더에 저장됩니다.

### 2단계 — (선택) GPT 기반 오타 교정

```bash
python src/gpt_based_weired_word_sensor.py
```

자막 텍스트에 포함된 오타나 이상한 단어를 GPT를 이용해 교정합니다. 현재 불안정한 모듈이므로, 기본적으로 이 단계는 건너뛰어도 됩니다. 실행 시 `OPENAI_API_KEY`가 필요합니다.

### 3단계 — 문장 분리 및 Vector DB 저장 형식 변환

```bash
python src/transcript_processing.py
```

수집된 자막을 SaT 모델로 문장 단위로 분리하고, 슬라이딩 윈도우를 적용해 chunk를 생성합니다. 각 chunk에 시작/종료 타임스탬프(HH:MM:SS)를 부착하고, Pinecone 업서트에 사용할 JSON 형식으로 변환합니다. 변환 결과는 `data/results/transcript_processing/` 폴더에 저장됩니다.

### 4단계 — Vector DB 저장

```bash
python src/Store_on_VectorDB.py
```

변환된 chunk 데이터를 Pinecone에 배치 업서트합니다. `video_link_target.yaml`에 설정한 인덱스와 네임스페이스에 저장됩니다.

### 5단계 — (별도) 시맨틱 검색

```bash
python src/Semantic_search.py
```

`query.json`에 입력한 자연어 쿼리로 Pinecone에서 관련 chunk를 검색합니다. 현재 이 스크립트는 추가 테스트가 필요한 상태이므로, **Pinecone 웹 콘솔의 통합 검색 기능** 사용을 권장합니다.

---

## 최종 출력 결과

### Vector DB 저장 결과

각 문장 chunk가 Pinecone의 지정한 인덱스/네임스페이스에 아래 형식의 레코드로 저장됩니다.

```json
{
  "id": "VIDEO_ID__101",
  "chunk_text": "여기에 해당 구간의 발언 내용이 들어갑니다.",
  "metadata": {
    "start": "00:24:13",
    "end":   "00:25:48",
    "title": "영상 제목"
  }
}
```

| 필드 | 설명 |
|---|---|
| `id` | `영상ID__청크번호` 형식의 고유 식별자 |
| `chunk_text` | 슬라이딩 윈도우로 묶인 문장 chunk 텍스트 |
| `metadata.start` | chunk 시작 시간 (HH:MM:SS) |
| `metadata.end` | chunk 종료 시간 (HH:MM:SS) |
| `metadata.title` | YouTube 영상 제목 |

### 검색 결과

자연어 쿼리를 입력하면 아래 정보가 반환됩니다.

| 반환 항목 | 설명 |
|---|---|
| 영상 제목 | 검색된 chunk가 속한 YouTube 영상의 제목 |
| 시작 시간 | 해당 chunk의 시작 지점 (HH:MM:SS) |
| 종료 시간 | 해당 chunk의 종료 지점 (HH:MM:SS) |
| 관련 텍스트 chunk | 쿼리와 의미적으로 가장 유사한 자막 구간 텍스트 |

### 중간 결과 파일

파이프라인 각 단계의 중간 결과는 `data/results/` 폴더 하위에 저장됩니다.

```text
data/results/
  Youtube_transcription/
    ID_Table.csv                          # 영상 ID 목록
    Youtube_video_info.json               # 영상 메타데이터
    Youtube_transcription.pkl             # 수집된 원본 자막
    Youtube_transcription_stacked_version.pkl
  transcript_processing/
    transcript_by_sentence.json           # 문장 분리 결과
    Full_text__input_of_weired_wrd_sensor.json
    vectorDB_upsert_data.json             # Pinecone 업서트용 최종 데이터
```

---

## 프로젝트 구조

```text
Youtube_Video_Search/
├── src/
│   ├── Youtube_transcription.py          # 1단계: 자막 및 메타데이터 수집
│   ├── gpt_based_weired_word_sensor.py   # 2단계(선택): GPT 오타 교정
│   ├── transcript_processing.py          # 3단계: 문장 분리 및 타임스탬프 추출
│   ├── Store_on_VectorDB.py              # 4단계: Pinecone 업서트
│   ├── Semantic_search.py                # 5단계(별도): 시맨틱 검색
│   └── Youtube_tool/
│       ├── ID_extraction.py              # YouTube 영상 ID 추출 유틸리티
│       └── Youtube_Collection.py         # YouTube API 호출 모듈
├── utils/
│   ├── file_path_reader.py               # 파일 경로 관련 유틸리티
│   ├── Pinecone_connection.py            # Pinecone 연결 유틸리티
│   └── text_pattern_filter.py            # 텍스트 패턴 필터링 유틸리티
├── data/
│   ├── raw_data/                         # 사용자가 직접 준비하는 입력 파일
│   └── results/                          # 파이프라인 단계별 중간 및 최종 결과
├── requirements.txt
├── env_example.txt
├── LICENSE
└── THIRD_PARTY_NOTICES.md
```

---

## 주의사항

- **SaT 처리 성능**: SaT 문장 분리는 대용량 자막 처리 시 연산 비용이 높습니다. 로컬 GPU가 충분하지 않은 경우, Google Colab 등 GPU 환경에서 3단계를 실행하는 것을 권장합니다.
- **`Semantic_search.py` 상태**: 현재 추가 수정이 필요합니다. 검색은 Pinecone 웹 콘솔의 통합 검색 기능을 사용해 주세요.
- **API 키 보안**: `.env` 파일 및 모든 API 키는 Git에 커밋하지 마세요.
- **Python 버전**: Python 3.10 이상을 사용해 주세요.

## 라이선스

- 본 프로젝트 코드: MIT License (`LICENSE` 파일 참고)
- 서드파티 라이브러리 라이선스: `THIRD_PARTY_NOTICES.md` 파일 참고
