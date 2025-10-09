# Project Guide

## SaT (Semantic-aware Segmentation) 실행 가이드

### 중요: SaT 모델 선택 가이드 ⚠️
**SaT 모델은 성능 차이가 매우 크므로, 반드시 Google Colab에서 고성능 모델을 사용해야 합니다.**

- **권장 모델**: `sat-3l` 또는 `sat-12l` (Large 모델)
- **비권장 모델**: `sat-1l-sm` (Small 모델) - 로컬 테스트용으로만 사용
- **성능 차이**: Large 모델은 문장 분할 정확도가 월등히 높으며, 의미 기반 세그먼테이션 품질이 우수합니다.

### GPU 리소스 요구사항
SaT 모델은 GPU 자원을 사용하여 실행하는 것을 권장합니다. 로컬 환경에 GPU가 없는 경우, Google Colab을 사용하여 실행하세요.

### 로컬에서 실행 (GPU 있는 경우)
```python
# config에서 use_gpu를 True로 설정
config = {
    ...
    "SaT_model": "sat-1l-sm",  # 테스트용만 사용
    "use_gpu": True,
    ...
}
```

### Google Colab에서 실행 (권장) ⭐
**프로덕션 환경에서는 반드시 Colab에서 고성능 모델을 사용하세요.**

1. Google Colab 노트북을 생성합니다
2. 런타임 > 런타임 유형 변경 > 하드웨어 가속기를 "GPU"로 설정
3. 필요한 패키지를 설치합니다
4. **고성능 모델로 설정**:
   ```python
   config = {
       ...
       "SaT_model": "sat-3l",  # 또는 "sat-12l" (더 높은 정확도)
       "use_gpu": True,
       ...
   }
   ```
5. SaT 처리를 Colab에서 실행하고 결과를 저장합니다
6. 저장된 결과 파일을 로컬로 다운로드하여 사용합니다

### 참고사항
- SaT는 한 번 실행하는데 시간이 오래 걸리므로, 중간 결과를 파일로 저장하는 것을 권장합니다
- `transcript_processing.py`의 `sentence_by_SaT_with_metadata()` 함수는 자동으로 중간 결과를 저장합니다
- **모델 선택이 최종 RAG 시스템의 품질에 큰 영향을 미치므로, 프로덕션에서는 반드시 Large 모델을 사용하세요**

## Youtube Download를 사용하려면 반드시 ffmpeg가 설치되어 있어야 한다.

## Pinecone Index-Namespace 관리 시스템 (2025-10-09 업데이트)

### 개요
이 프로젝트는 각 YouTube 비디오마다 독립적인 Pinecone 설정(index, namespace, embedding model 등)을 지원합니다.

### 구조
- **Global Config**: 프로젝트 전체에 공통으로 적용되는 설정
  - SaT 모델 설정 (model, threshold, concat_length, use_gpu)
  - Pinecone API Key
- **Video Config**: 각 비디오별로 설정되는 Pinecone 관련 설정
  - 위치: `data/external_data/video_link_target.yaml`
  - 형식:
    ```yaml
    https://youtube.com/watch?v=VIDEO_ID:
      index_name: "developer-quickstart-py"
      namespace: "test"
      cloud: "aws"
      region: "us-east-1"
      embed:
        model: "llama-text-embed-v2"
        field_map:
          text: "chunk_text"
      Author: "채널명"
      Comment: "비디오 설명"
    ```

### Index-Namespace별 ID 관리
프로젝트는 각 index-namespace 조합별로 독립적인 ID tracking을 수행합니다:

1. **같은 index-namespace를 공유하는 비디오들**
   - Global하게 증가하는 ID counter를 공유
   - 예: Video1(index1/ns1): IDs 101-105, Video2(index1/ns1): IDs 106-110

2. **다른 index-namespace를 사용하는 비디오들**
   - 독립적인 ID sequence를 가짐
   - 예: Video3(index2/ns2): IDs 51-55 (Video1, Video2와 무관)

3. **ID 형식**: `{video_id}__{increasing_count}`
   - 예: `EWvNQjAaOHw__101`, `EWvNQjAaOHw__102`, ...

### 주요 함수

#### `utils/Pinecone_connection.py`
- **`get_index_host_mapping(pc: Pinecone)`**: 모든 index의 이름-host 매핑을 반환
  - 중복 index 이름 감지 및 경고

#### `utils/file_path_reader.py`
- **`load_video_config()`**: video_link_target.yaml에서 비디오별 config 로드

#### `src/transcript_processing.py`
- **`get_namespace_len(video_config, dict_of_pc_index)`**: 각 index-namespace의 현재 vector 개수 반환
- **`transcript_to_record_batch()`**: 비디오별 config를 사용하여 VectorDB record 생성, index-namespace별 ID tracking

### 실행 흐름
1. `load_video_config()`로 비디오별 Pinecone 설정 로드
2. `get_index_host_mapping()`으로 index-host 매핑 생성
3. 각 index에 대해 `connect_to_Index()`로 연결 객체 생성
4. `dict_of_pc_index`에 모든 index 객체 저장
5. 비디오 처리 시 해당 비디오의 config에서 index_name, namespace 추출
6. Index-namespace별로 독립적인 ID counter 유지하며 데이터 처리

### 주의사항
- 각 비디오의 config에 반드시 `index_name`과 `namespace`가 정의되어 있어야 함
- 동일한 index-namespace를 사용하는 비디오들은 ID가 중복되지 않도록 자동 관리됨
- Host는 수동 입력 대신 `get_index_host_mapping()`을 통해 자동으로 조회

---

## Pinecone 414 에러 해결 (2025-10-09)

### 문제 상황
`Store_on_VectorDB.py`에서 대량의 레코드를 Pinecone에 upsert할 때 다음 에러가 발생:
```
pinecone.exceptions.exceptions.PineconeApiException: (414)
Reason: Request-URI Too Large
```

### 원인
- `check_vector_id_existence()` 함수가 **모든 레코드 ID를 한 번에 URL에 담아서** Pinecone API에 요청
- 한 영상에 수천 개의 레코드가 있을 경우 URL이 너무 길어짐 (URL 길이 제한 초과)
- 예: 3,000개 레코드 → 3,000개 ID를 모두 `fetch()` 요청 → 414 에러

### 해결 방법 (src/Store_on_VectorDB.py:305-308)
**전체 레코드를 체크하는 대신, 첫 번째와 마지막 레코드만 샘플링하여 체크**

```python
# 변경 전 (문제 발생)
record_exist = check_vector_id_existence(
    pc_index=pc_index,
    namespace=namespace,
    vector_id_list=list(map(lambda x: x["id"], records))  # 모든 레코드 ID
)

# 변경 후 (해결)
# Check only first and last record to avoid 414 error
sample_ids = [records[0]["id"], records[-1]["id"]] if len(records) > 1 else [records[0]["id"]]
record_exist = check_vector_id_existence(
    pc_index=pc_index,
    namespace=namespace,
    vector_id_list=sample_ids  # 첫/마지막 ID만
)
```

### 로직
- **가정**: 동일 영상의 첫 번째와 마지막 레코드가 존재하면, 전체 영상이 이미 업로드된 것으로 간주
- **합리성**: 실제 운영에서 동일 영상의 일부만 업로드되는 경우는 거의 없음
- **효과**: URL 길이를 수천 개에서 2개로 대폭 축소

### 추가 개선 사항
배치 업로드 진행 상황 로깅 추가:
```python
print(f"Upserting {len(records)} records for video {video_id} in {len(batch_split_list)} batches...")
for idx, batch in enumerate(batch_split_list, 1):
    pc_index.upsert_records(namespace, batch)
    print(f"  Batch {idx}/{len(batch_split_list)} uploaded ({len(batch)} records)")
```
