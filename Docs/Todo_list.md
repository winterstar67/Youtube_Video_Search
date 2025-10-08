### 작성 시간2025-10-02 00:24
1. pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu126를 해야 wtpsplit 사용이 가능하다.
2. Transcripts를 받고 싶은 동영상 리스트를 설정하여, 해당 동영상들의 자막을 받는 모듈을 하나 만든다.
3. Pinecone을 Free plan으로 시작했고, 한 번 사용해봐야 됨
4. 다국어 지원하는 embedding 모델이 지금 나의 목적에 중요하다 (chatgpt에 질문하듯이 어떤 동영상의 어떤 시간대에서 이 말을 했었지? 를 검색하기 위함임. 근데 정이 성능이 떨어지면 영어 위주의 embedding model이라도 사용해야 됨)
5. 전체적인 pipeline 한 번 빠르게 만들어보자.

자막 퀄리티도 둘 째 치고, 일단 Vector DB에 넣고 빠르게 searching하는 코드를 작성하자.



현재 부딪힌 한계점:
- 자동 자막의 일부 오타(ChatGPT를 chpt 라고 하는 경우), 마침표가 없는 경우, 굳이 없어도 되는 말(okay, umm...)이 있다.
    - 자동 자막을 전처리 할 것인가?
    - 아니면 처음부터 언어가 잘 나오도록 Whisper같은 모델로 시도해본다. (유튜브 자동자막 자체를 무엇으로 생성하는지는 잘 모르겠음. Whisper 같은 딥러닝 모델이 자동 번역보다 잘할지 한 번 테스트 해봐야됨.)
        - 이 프로젝트의 중요한 점 중 하나가 내가 찾고싶던 요소가 어떤 동영상의 "몇 분 지점"인지를 알아야 하는데, 그 기능을 제공해주는지 잘 모르겠음.

만약 자동 자막 전처리를 한다면, 자동 자막(전처리 전)과 영어 자막이 올라온 자막(Label) 가 둘 다 있는 동영상들을 모아서, 전처리 후의 성능이 어떤지 `자동 자막 - Label`과 `전처리된 자동 자막 - Label`을 비교해서 유의미하게 좋아지는지를 파악해야 됨.


### 작성 시간 2025-10-04 19:45
## SaT 적용해서 문장 단위로 split함과 동시에 해당 문장의 시간 대를 같이 저장해서 tracking하는 방법
# 맨 처음 split된 상태인 원본 데이터를 가지고 있는다
# 마찬가지로 원본 split의 start와 duration을 가지고 있는다
# 그리고 concat하고 split한 결과를 가져온다.

# 원본 split 데이터 각각을 좌측에서부터 align 시켜 나가면서 start와 duration을 확인한다  ## 이미 처리한 부분들은 삭제하면서 계속 진행해 나가기?
    - 원본 문장이 다 맞춰질 때까지 (혹시 모르니 공백(space)은 아예 없애는 편이 나으려나?)
    - 원본이 "like to do it what about this" 이고 문장 합치고 split했을 때 ["I like to", "do it", "what about this"] 라면 처음 like부터 계속 매칭하면서 about this 나올 때 까지 matching 과정을 진행

### 작성 시간 2025-10-05
## Pinecone Vector DB에 데이터 넣기


### 작성 시간 2025-10-06 1:42
## namespace list 를 반환하는 함수 따로, 그리고 해당 list안에 내가 원하는 namespace가 있는지 확인하는 function을 각각 2개를 만들지, 아니면 그냥 바로 내가 원하는 namespace가 있는지 확인하는 function만 만들지  고민중임

## Metadata에 Video 정보도 넣긴 해야됨.  ->  key값에 video link가 아니라 video title을 넣던가 해야 됨.
    - Author, Chennel, Video title 같이 동영상의 meta data를 넣어야 됨.

### 작성 시간 2025-10-06
## src/Store_on_VectorDB.py 에 def main() 부분을 작성해야 함

## 자막 quality를 최대한 더 올려야 한다 (의미 없는 text filtering이 필요함)

## 나머지 retrieval 과정을 완성해서 pipeline을 구축한다.
    - https://docs.pinecone.io/guides/get-started/quickstart

## Airflow를 사용해본다.

## 작성 시간 2025-10-06 19:05
    - 먼저 자동 자막과 없어도 문장의 의미에 영향을 주지 않는 text 패턴들을 찾으라고 지시하기(예: uh, hmm, okay). 그리고  쓸데없는 패턴을 가진 경우, 어떻게 처리할지 물어보기. 처리 코드를 준다면 하나의 string text를 받아서 처리하는 파이썬 코드를 작성해달라고 요청하기
        - 함부로 삭제하면 안됨. 왜냐하면, uh를 삭제했다가 uh라는 text를 포함한 단어에 까지 영향을 미칠 수 있기 때문임. 
        - ChatGPT thinking mode로 물어보기

    - ID Table 만들기
    - MetaData가 유튜브 동영상에 따라 중복되는 경우는, Metadata에는 동영상 id 같은 것만 넣어두고 나머지는 ID Table 참조하도록 변경하기
    - Vector 자체의 ID에 대해서, 그냥 {youtubeID}_{increasing count} 형식으로 가야할듯

## 작성 시간 2025-10-06 23:56
    - Vector DB에 들어가는 chunk_text 혹은 vector의 개별 id를 {동영상_id}_{increasing_count} 형식에 맞춰서 변형하는 작업 필요

## 작성 시간 2025-10-07 02:25
    - 유튜브 말고도 Article과 Paper도 RAG 적용하는 것을 고려해보자.
    - https://huggingface.co/nvidia/NV-Embed-v2 의 embedding vector도 고려해보자(ChatGPT Research로 찾은 embedding model임.)


## 작성 시간 2025-10-07 12:32
    - 현재 문제: 3개 문장을 연결하는 바람에 char 개수가 10개 이하인 경우를 catch하지 못하고 있음
        - 그냥 데이터 전처리와 Vector DB에 저장하는 코드 파일을 그냥 분리해야겠다.
        - 데이터 전처리는 추후 계속 변경될 여지가 있어서 별도 파일로 관리하는 편이 낫겠음.


## Idea
지금은 문장 3개를 연이어 붙여서 하나의 문장으로 만드는 작업을 하였다.
    - 문장 3개 말고 문장 5개, 7개까지 붙여서 하나의 문장으로 만들고, 이것도 vectordb에 동시에 넣자.
    - 그렇게 해서 retrieve를 했을 때 나온 문장 중에서 문장 3개 통합 문장이 문장 5개 통합 문장 내에 포함되었다면 문장 3개 짜리는 버린다.
        - 이런 식으로 최대한 확보 가능하면서도 길이가 긴 문장을 retrieve 하는 전략은 어떨까?
    - 만약 문장을 3개가 아니라 더 많이 이어붙이도록 하면 문제가 겹치는 부분이 너무 많이 나옴 - 절반 가량이 겹침.
        - Jaccard Similarity 사용해서 처리해야 할 수도 있음.
        - 아니면 sliding_interval_size를 늘려야 할듯.

ChatGPT에 제목, description과 함께 자막을 최대 5,000자 만 넣고 오타다 싶은 것만 pattern 추려서 {} 형태로 mapping하는 json 반환하도록 만들어야 됨.
    - 수작업으로 rulebase로 하는 것은 여러 동영상에 대해서 할 수 없어서 scalable하지 않음.


다시 LLM 돌려서 similarity 높다고 나온 후보들 중에 어느 것이 가장 관련이 있어 보이는가? 를 다시 물어보도록 하자.
    - 이게 ReRank 개념이라고 함.
    - 기존의 score화 해서 얻어오는 것은 embedding vector 기반으로 cos similarity를 보는 것이고, 사람들도 이게 잘 작동 안하는 경우가 많아서 한계를 부딪히고 완전하지 않다는 것을 아니까, 보완하기 위해서 이런 것을 가져온듯.

## 2025 10 08 01:06
    - SaT 적용하고 각 text마다 strip() 적용해야됨.
        - 'concatenated': separator.join(sentences[i-concat_length//2 : i+concat_length//2+1].strip().replace("  ", " ")) 부분에 .strip().replace("  ", " ")를 적용함.
            - 이렇게 했을 때, start time이 이상하게 잡혔던 것 같음.
            - "text":sentence.strip().replace("  ", " "), 이렇게 적용함.
    - colab으로 보니까 How I use LLMs에서 current_result에 아래 내용이 중복됨
        - "so first of all the web page that I have pulled up here is chp.com  now as you might know chpt it was developed by openai and deployed in 2022 so this was the first time that people could actually just kind of like talk to a large language model through a text interface and this went viral and over all over the place on the internet and this was huge now since then though the ecosystem has grown a lot"
            -> 이거 의도한대로 적용되는 것이 맞았음.

    - 전체적으로 File의 각 function별 arguments의 type 선언과 Docs가 올바르게 되었는지 점검해야됨

## 2025-10-08 13:32
    - start, end를 시간, 분, 초로 변환하기 (그래야 유튜브에서 더 빠르게 찾지)
    - 찾아보면 텍스트와 실제 유튜브에 들어가서 확인한 시간이 자꾸 엇나감. start, end를 주는 시간이 잘못되었나?
        - 최대한 start, end 붙일 때는 원본 텍스트를 유지하자. -> text_list_preprocessing를 나중에 적용하자.
        - SaT는 한 번 실행하는데 많이 걸리니까 중간 결과로 저장해놓자.
    - 동영상도 download_video 기능 만들어서 sleep 많이 걸어두고(따로 진행하도록) 다운받도록 하는 기능도 추가하자