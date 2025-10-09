현재 부딪힌 한계점:
- 자동 자막의 일부 오타(ChatGPT를 chpt 라고 하는 경우), 마침표가 없는 경우, 굳이 없어도 되는 말(okay, umm...)이 있다.
    - 자동 자막을 전처리 할 것인가?
    - 아니면 처음부터 언어가 잘 나오도록 Whisper같은 모델로 시도해본다. (유튜브 자동자막 자체를 무엇으로 생성하는지는 잘 모르겠음. Whisper 같은 딥러닝 모델이 자동 번역보다 잘할지 한 번 테스트 해봐야됨.)
        - 이 프로젝트의 중요한 점 중 하나가 내가 찾고싶던 요소가 어떤 동영상의 "몇 분 지점"인지를 알아야 하는데, 그 기능을 제공해주는지 잘 모르겠음.

    -> (일부 완료) 일부 패턴에 대해서는 처리 했고 GPT로 이상한 text 패턴 캐치해서 목록을 만들고자 한다. (2025-10-08-22:46)


만약 자동 자막 전처리를 한다면, 자동 자막(전처리 전)과 영어 자막이 올라온 자막(Label) 가 둘 다 있는 동영상들을 모아서, 전처리 후의 성능이 어떤지 `자동 자막 - Label`과 `전처리된 자동 자막 - Label`을 비교해서 유의미하게 좋아지는지를 파악해야 됨.
    -> (미완) 아직 시도를 안함 (2025-10-08-22:46)

## 자막 quality를 최대한 더 올려야 한다 (의미 없는 text filtering이 필요함)
    - (부분 완료) (2025-10-08-22:46)

## 작성 시간 2025-10-06 19:05
    - 먼저 자동 자막과 없어도 문장의 의미에 영향을 주지 않는 text 패턴들을 찾으라고 지시하기(예: uh, hmm, okay). 그리고  쓸데없는 패턴을 가진 경우, 어떻게 처리할지 물어보기. 처리 코드를 준다면 하나의 string text를 받아서 처리하는 파이썬 코드를 작성해달라고 요청하기
        - 함부로 삭제하면 안됨. 왜냐하면, uh를 삭제했다가 uh라는 text를 포함한 단어에 까지 영향을 미칠 수 있기 때문임.
        - ChatGPT thinking mode로 물어보기
        - (진행 중) gpt_based_weired_word_sensor.py에서 진행 예정 (2025-10-09 21:12)
            - 현재 기능: GPT-4o-mini로 각 영상의 첫 6000자를 분석하여 오타 감지
            - 예정 기능 변경: 출력 형식을 영상별로 구조화
                ```json
                {
                    "영상_id_1": {
                        "gpt가_선택한_어색한_오타_단어_1": "내가_바꾼_단어_1",
                        "gpt가_선택한_어색한_오타_단어_2": "내가_바꾼_단어_2"
                    },
                    "영상_id_2": {
                        "오타_단어_1": "수정_단어_1"
                    }
                }
                ```
            - 이 형식으로 변경하여 영상별 오타 패턴 관리 용이하게 개선 예정

    - ID Table 만들기
        - (부분 완료) csv 파일 이름만 Youtube_transcription.csv에서 ID_Table.csv로 바꾸면 될듯. (2025-10-08-22:46)

## 작성 시간 2025-10-07 02:25
    - 유튜브 말고도 Article과 Paper도 RAG 적용하는 것을 고려해보자.
        - (미완) 진행 예정 (2025-10-08-22:46)
    - https://huggingface.co/nvidia/NV-Embed-v2 의 embedding vector도 고려해보자(ChatGPT Research로 찾은 embedding model임.)
        - (미완) (2025-10-08-22:46)
            - custom embedding model 을 사용하는 경우에 대한 파이프라인 하나 더 만들어야 함. pinecone도 chunk_text가 아니라 vector를 입력하는 function 으로 변경해야 됨.


## Idea
지금은 문장 3개를 연이어 붙여서 하나의 문장으로 만드는 작업을 하였다.
    - 문장 3개 말고 문장 5개, 7개까지 붙여서 하나의 문장으로 만들고, 이것도 vectordb에 동시에 넣자.
        - (완료) (2025-10-08-22:46)
    - 그렇게 해서 retrieve를 했을 때 나온 문장 중에서 문장 3개 통합 문장이 문장 5개 통합 문장 내에 포함되었다면 문장 3개 짜리는 버린다.
        - 이런 식으로 최대한 확보 가능하면서도 길이가 긴 문장을 retrieve 하는 전략은 어떨까?
        - (미완) (2025-10-08-22:46)
    - 만약 문장을 3개가 아니라 더 많이 이어붙이도록 하면 문제가 겹치는 부분이 너무 많이 나옴 - 절반 가량이 겹침.
        - Jaccard Similarity 사용해서 처리해야 할 수도 있음.
        - 아니면 sliding_interval_size를 늘려야 할듯.

ChatGPT에 제목, description과 함께 자막을 최대 5,000자 만 넣고 오타다 싶은 것만 pattern 추려서 {} 형태로 mapping하는 json 반환하도록 만들어야 됨.
    - 수작업으로 rulebase로 하는 것은 여러 동영상에 대해서 할 수 없어서 scalable하지 않음.
    - (미완) (2025-10-08-22:46)


    - 전체적으로 File의 각 function별 arguments의 type 선언과 Docs가 올바르게 되었는지 점검해야됨
        - (미완) (2025-10-08-22:46)

    - 동영상도 download_video 기능 만들어서 sleep 많이 걸어두고(따로 진행하도록) 다운받도록 하는 기능도 추가하자
        - (미완) (2025-10-08-22:46)

    - 웹 만들기
        - 검색 웹이 있고 저장 웹이 있다.
            - 검색은 이미 VectorDB에 있는 것으로 만들기
            - 저장은 사전에 동영상 링크 받고, 해당 링크(동영상)의 제목, 저자, 이외 comment 받도록 하기
        - (미완) Claude code로 맨 처음 요청을 해서 초안은 만들었고, 검증과 수정 과정을 반복해야 됨. (2025-10-08-22:46)

    - GPT를 사용해서 Retrieval 결과 다듬는 모듈 만들기
        - (미완) (2025-10-08-22:46)

    - blog article이면 VectorDB에 저장할 때, metadata에 블로그 포스트 제목과 Author도 넣기
        - (부분 완료) video는 그렇게 해 놓았고, blog는 아직 받는 기능도 업음 (2025-10-08-22:46)

    - 현재까지 파악한 Pinecone 기능들을 저장하자.

    - 자막 퀄리티를 좋게 만들 방법을 계속해서 생각해보자.
        - 각 동영상마다 자막 text의 [:5000]를 GPT로 넘겨서 말이 안되는 text 패턴 파악하고 처리하는 코드를 작성하자.
            - 이것은 pipeline이 아니라 내가 최대한 많은 동영상에 대해서 처리하면서 따로 진행해야 하는 코드로써 .py 파일 만들어서 사용해야 한다.

    - start, end 시간을 찾는 코드를 작성할 때의 유의사항:
        - 이 작업을 진행할 때는 반드시 원본 자막에 전처리라거나 어떠한 수정도 가해서는 안된다. SaT를 적용한 것도 마찬가지이다. SaT로 분리 전과 후의 텍스트가 한 글자라도 바뀌면 안된다.

    - 각 File의 Config 파일은 그냥 .json으로 만들어라. 그래야 웹 페이지에서도 접근이 쉬울 것이다.
        - config는 각 video 마다 따로따로 작성해야 할듯.
    
    - csv 파일 이름만 Youtube_transcription.csv에서 ID_Table.csv로 바꾸면 될듯. (2025-10-08-22:46)

    - 전체적으로 File의 각 function별 arguments의 type 선언과 Docs가 올바르게 되었는지 점검해야됨

    - 동영상 수집기를 "src/Youtube_tool/Youtube_video_downloader.py" 에 만들기

## 작성 시간 2025-10-09
### Video별 Pinecone Config 리팩토링 작업 (2025-10-09)

#### 완료된 작업:
1. **utils/file_path_reader.py**
    - (완료) `load_video_config()` 함수 추가 - video_link_target.yaml에서 video별 config 로드

2. **utils/Pinecone_connection.py**
    - (완료) `get_index_host_mapping()` 함수 추가 - pc.list_indexes()로 index-host 매핑 생성
    - (완료) 중복 index 처리 로직 추가

3. **src/transcript_processing.py**
    - (완료) Global config에서 Pinecone 관련 key 제거 (index_name, namespace, cloud, region, embed, Author, Comment)
    - (완료) `get_namespace_len()` 함수 수정 - video_config와 dict_of_pc_index를 받아서 index-namespace별 vector count 반환
    - (완료) `transcript_to_record()` 함수 수정 - field_map 파라미터 추가
    - (완료) `transcript_to_record_batch()` 함수 완전 재작성 - video별 config 사용, index-namespace별 독립적인 ID tracking
    - (완료) `main()` 함수 수정 - dict_of_pc_index 생성 및 video_config 로드
    - **(검토 필요)** Claude Code로 작업했으므로 동작 확인 필요

#### 남은 작업:

4. **src/Semantic_search.py**
    - (미완) Global config["namespace"] 사용 제거 필요 (Line 113)
    - (미완) video별 config를 사용하도록 수정
    - (미완) utils의 input_file_loader 사용하도록 변경

5. **src/Store_on_VectorDB.py**
    - (미완) Global config["namespace"] 사용 제거 필요 (Lines 160, 178, 194, 220, 273, 301, 404)
    - (미완) Global config["cloud"], config["region"] 사용 제거 필요 (Lines 263-264)
    - (미완) Global config["embed"]["model"], config["embed"]["field_map"] 사용 제거 필요 (Lines 266-267, 358)
    - (미완) video별 config를 사용하도록 수정
    - (미완) utils의 input_file_loader 사용하도록 변경
    - (미완) dict_of_pc_index를 사용하도록 수정

6. **app/main.py**
    - (미완) Global config["Author"], config["Comment"] 사용 제거 필요 (Lines 173-174)
    - (미완) video별 config를 사용하도록 수정
    - (미완) FastAPI endpoint에서 video별 config 처리 로직 추가

7. **전체 파일 검토**
    - (미완) 모든 파일에서 utils의 file_path_reader 함수들 (input_file_loader, output_file_loader, save_result_to_file) 사용하는지 확인
    - (미완) video별 index-namespace 설정이 올바르게 동작하는지 테스트

#### 참고사항:
- video_link_target.yaml 구조가 변경됨: `{video_URL: {index_name, namespace, cloud, region, embed, Author, Comment, ...}}`
- 같은 index-namespace를 사용하는 video들은 global ID를 공유하며, 다른 index-namespace는 독립적인 ID sequence를 가짐
- ID 형식: `{video_id}__{increasing_count}` (예: `EWvNQjAaOHw__101`)
