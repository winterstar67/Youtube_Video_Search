"""
oreder in pipeline: Second (2)
    - Previous_file: Youtube_transcription.py
    - Next_file: Store_on_VectorDB.py

Function:
    1. 자막을 Youtube_transcription.py에서 받아와서, SaT를 사용하여 문장 단위로 모아서 다시 split를 함.
    2. 문장 단위로 split할 때, 각 문장마다 시작 시간과 종료 시간을 추가함.
    3. transcript_processing.py에서 받은 데이터를 VectorDB에 저장되는 형태로 변환

Input: 
    - File directory: data/results/Youtube_transcription.pkl
        - Key: each_video_link
        - Value: transcription of each video
    - {"each_video_link": "transcription of each video"}
Output:
    - File directory: data/results/transcript_by_sentence.pkl
        - Key: each_video_link
        - Value: transcription of each video by sentence
    - VectorDB에 저장되는 format의 data


Todo list:
    - SaT의 seg.split() 함수에서 threshold의 역할이 무엇인지 파악해야 함. 2025-10-05

Guidance:
    - ID 부여 방식:
        - 서로 다른 youtube video, Docs 등 모든 source에 대해 global한 increasing count를 사용
        - 형식: {source_identifier}__{global_id}
        - 예시: Docs1__id1, Docs2__id2, youtube_video5__id3, Docs1__id4

    - Debugging 시:
        - 개별 source별로 debugging이 필요한 경우, source identifier로 filtering
        - 형식: Docs{num} 혹은 youtube_video{num}
        - Filtering 후 index reordering을 통해 debugging 수행

transcript_processing.py
"""

import os
import pickle
import json
from wtpsplit import SaT
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime
import sys
import dotenv
from pinecone import Pinecone

dotenv.load_dotenv()

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

sys.path.append(parent_dir)
from utils import text_pattern_filter
from utils.file_path_reader import file_loader, save_result_to_file, load_video_config
from utils.Pinecone_connection import connect_to_Index, connect_to_Pinecone, get_index_host_mapping
from Youtube_tool.ID_extraction import extract_video_id
import json

SCRIPT_NAME:str = os.path.splitext(os.path.basename(__file__))[0]  # "transcript_processing"
INPUT_FILE_PATH:str = os.path.join(parent_dir, "data", "results", "Youtube_transcription")
INPUT_FILE_NAME:str = "Youtube_transcription"
INPUT_FILE_EXTENSION:str = "pkl"
INPUT_FILE_PATH_WITH_NAME:str = os.path.join(INPUT_FILE_PATH, INPUT_FILE_NAME + "." + INPUT_FILE_EXTENSION)

OUTPUT_FILE_PATH:str = os.path.join(parent_dir, "data", "results", SCRIPT_NAME)
OUTPUT_FILE_NAME:str = f"transcript_by_sentence"
OUTPUT_FILE_EXTENSION:str = "json"

config = json.load(open(os.path.join(parent_dir, "data", "raw_data", "transcript_processing_config.json"), "r"))
if (config["use_gpu"]).lower()=="false":
    config["use_gpu"] = False
elif (config["use_gpu"]).lower()=="true":
    config["use_gpu"] = True
else:
    raise ValueError("use_gpu must be 'False' or 'True'")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

def YouTubeTranscript_to_text(YouTubeTranscript:YouTubeTranscriptApi) -> str:
    """
    Convert YouTubeTranscript to text
    Input: YouTubeTranscript type
        - example: 
          [
          FetchedTranscriptSnippet(text="hi everyone so I've wanted to make this", start=0.719, duration=4.681),
          FetchedTranscriptSnippet(text='video for a while it is a comprehensive', start=2.76, duration=5.32),
          ...
          ]

    Output: text type
        - example: "hi everyone so I've wanted to make this video for a while it is a comprehensive"
    """
    text = ""
    for snippet in YouTubeTranscript:
        text += " " + snippet.text
    return text

def sentence_by_SaT(text:list[str], model:str=config["SaT_model"], threshold:float=config["SaT_threshold"], use_gpu:bool=False) -> list[str]:
    """
    Split text into sentences using SaT
    Input: text type
        - example: "hi everyone so I've wanted to make this video for a while it is a comprehensive"
    Output: list[str] type
        - example: ["hi everyone so I've wanted to make this video for a while", "it is a comprehensive", ...]
    """
    seg:list[str] = SaT(model)
    if use_gpu:
        seg.half().to("cuda")
    else:
        pass
    raw = seg.split(text, threshold=threshold)
    return raw

def concatenate_with_neighbors_detailed(sentences:list[dict], separator:str=' ', concat_length:int=3) -> list[dict]:
    """
    리스트의 각 요소를 앞뒤 요소와 연결하는 함수 (구분자 옵션 포함)

    Parameters:
    -----------
    sentences : list[dict]
        문장들의 리스트 (각 dict는 'text' 키를 포함)
    separator : str
        요소들 사이에 넣을 구분자 (기본값: 공백 ' ')
    concat_length : int
        연결할 요소의 개수 (기본값: 3)
        - 반드시 odd number로 설정해야 함.

    Returns:
    --------
    list[dict]
        각 연결 결과를 포함한 리스트
        - 원본 메타데이터(start, end, title, url 등)를 유지
        - 'text' 필드에 concatenated된 텍스트를 저장
    """
    if concat_length % 2 == 0:
        raise ValueError("concat_length must be an odd number")

    if len(sentences) < concat_length:
        return []

    results = []

    for i in range(concat_length//2, len(sentences) - concat_length//2):
        # 중심 문장의 메타데이터를 복사
        result = sentences[i].copy()

        # concatenated 텍스트 생성
        text_parts = [sentences[j]['text'] for j in range(i-concat_length//2, i+concat_length//2+1)]
        result['text'] = separator.join(text_parts)

        results.append(result)

    return results

def text_list_preprocessing(text_list:list[dict], concat_length:int) -> list[dict]:
    """
    Preprocess text list
    Input: text_list type
        - example: [{"text": "hi everyone...", "start": 0.0, "end": 5.4, ...}, ...]
    Output: list[dict] type
        - example: [{"text": "hi everyone...", "start": 0.0, "end": 5.4, ...}, ...]
    """
    filtering_short_text = text_pattern_filter.remove_filler_words(text=text_list)
    filtering_short_text = text_pattern_filter.remove_short_text(text_list=filtering_short_text, min_length=10)
    concatenated_text_by_SaT = concatenate_with_neighbors_detailed(sentences=filtering_short_text, separator=' ', concat_length=concat_length)

    return concatenated_text_by_SaT

def seconds_to_hms(seconds:float) -> str:
    """
    Convert seconds to hh:mm:ss format

    Parameters:
    -----------
    seconds : float
        Time in seconds (e.g., 125.5)

    Returns:
    --------
    str
        Time in hh:mm:ss format (e.g., "00:02:05")
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def attach_start_end(concatenated_text_by_SaT:list[str], youtube_transcripts_data:dict[str, dict[str]], concat_length:int) -> list[str]:
    """
    Attach start and end to text list
    Input: concatenated_text_by_SaT, youtube_transcripts_data
        - example: ["hi everyone so I've wanted to make this video for a while", "it is a comprehensive", ...]
        - youtube_transcripts_data: dict type
            - example: {
                "transcription": [
                ...
                ],
                "video_info": {
                    ...
                }
            }
    Output: list[str] type
        - example: ["hi everyone so I've wanted to make this video for a while", "it is a comprehensive", ...]
    """
    raw_index, sents_with_metadata = 0, [] 

    for sentence in concatenated_text_by_SaT: # Each sentence in one video
        # sentence = _sentence['concatenated'] # 앞 뒤 setence를 concat함에 따라 concatenated_text_by_SaT의 'text'는 previous, current, next, concatenated를 가지고 있음. 여기서 필요한 것은 concatenated임.
        raw_index_at_sentence, start_at_sentence = raw_index, 0 # raw_index_at_sentence: raw_index, start_at_sentence: 0, initionalization

        for raw_split_string in youtube_transcripts_data['transcription'][raw_index_at_sentence:]: # Each split string in one video
            raw_index += 1 # raw_index: 1, 2, 3, ... - to count next index
            
            # 시작 시간 기록
            if (start_at_sentence==0):
                start_at_sentence = raw_split_string.start
            else: 
                pass

            # 종료 시간 기록
            if (raw_split_string.text in sentence): # 진행 하면서 원본 텍스트가 SaT 텍스트에 포함되는 경우 pass
                pass
            
            else:
                end_at_sentence = raw_split_string.start + raw_split_string.duration
                sents_with_metadata.append({
                    "text":sentence.strip().replace("  ", " "),
                    "start":seconds_to_hms(start_at_sentence),
                    "end":seconds_to_hms(end_at_sentence),
                    "title":youtube_transcripts_data['video_info']['title'],
                    "channelTitle":youtube_transcripts_data['video_info']['channelTitle'],
                    "publishedAt":youtube_transcripts_data['video_info']['publishedAt'],
                    "concat_length":concat_length
                })
                break

    return sents_with_metadata


def sentence_by_SaT_with_metadata(input_transcript:dict[str, dict[str]], model:str=config["SaT_model"], threshold:float=config["SaT_threshold"], concat_length:int=config["concat_length"], use_gpu:bool=False) -> dict[str, list[dict]]:
    """
    Split text into sentences using SaT with metadata
    Input:
        - input_transcript example: 
          {
            "EWvNQjAaOHw": {
                "transcription": [
                ...
                ],
                "video_info": {
                    ...
                }
            }
          }
        - model example: "sat-1l-sm"
        - threshold example: 0.35
        - concat_length example: 3
    Output: dict[str, list[dict]] type
        - example: 
          [
          {"text": "hi everyone so I've wanted to make this video for a while", "start": 0.719, "end": 5.4},
          {"text": "it is a comprehensive", "start": 5.4, "end": 10.72},
          ...
          ]
    """
    global INPUT_FILE_PATH, INPUT_FILE_NAME, INPUT_FILE_EXTENSION
    global OUTPUT_FILE_PATH, OUTPUT_FILE_NAME, OUTPUT_FILE_EXTENSION
    result:dict[str, list[dict]] = {}
    full_text_dict:dict[str, str] = {}

    for youtube_id, youtube_transcripts_data in input_transcript.items(): # Each video

        Full_text:str = YouTubeTranscript_to_text(youtube_transcripts_data['transcription']) # "hi everyone so I've wanted to make this video for a while it is a comprehensive"
        full_text_dict[youtube_id] = Full_text

        segmented_text_by_SaT:list[str] = sentence_by_SaT(text=Full_text, model=model, threshold=threshold, use_gpu=use_gpu) # ["hi everyone so I've wanted to make this video for a while", "it is a comprehensive", ...]
        """
        segmented_text_by_SaT == ["hi everyone so I've wanted to make this video for a while", "it is a comprehensive", ...]
        """

        # start end를 먼저 붙이고, 그 다음에 text_list_preprocessing을 적용하여 원본 타임스탬프를 유지
        sents_with_metadata = attach_start_end(concatenated_text_by_SaT=segmented_text_by_SaT, youtube_transcripts_data=youtube_transcripts_data, concat_length=concat_length)
        """
        sents_with_metadata == [
            {"text": "uh hi everyone so I've wanted to make this video for a while", "start": 0.719, "end": 5.4},
            {"text": "hmm, it is a comprehensive", "start": 5.4, "end": 10.72},
            ...
        ]
        """
        sents_with_metadata = text_list_preprocessing(sents_with_metadata, concat_length=concat_length)
        """
        sents_with_metadata == [
            {"text": "hi everyone so I've wanted to make this video for a while", "start": 0.719, "end": 5.4},
            {"text": "it is a comprehensive", "start": 5.4, "end": 10.72},
            ...
        ]
        """

        result[youtube_id] = sents_with_metadata

    save_result_to_file(result=full_text_dict, file_path=OUTPUT_FILE_PATH, file_name="Full_text__input_of_weired_wrd_sensor", file_extension="json")
    return result

# === namespace length function===
def get_namespace_len(video_config:dict, dict_of_pc_index:dict[str, "Pinecone.Index"]) -> dict[str, dict[str, int]]:
    """
    Get namespace length for each index-namespace pair from video config

    Input: video_config, dict_of_pc_index
        - video_config: dict type
            - Keys: video URLs
            - Values: dict containing "index_name" and "namespace"
            - example: {
                "https://youtube.com/watch?v=xxx": {
                    "index_name": "developer-quickstart-py",
                    "namespace": "test",
                    ...
                },
                ...
              }
        - dict_of_pc_index: dict[str, Pinecone.Index]
            - example: {
                "developer-quickstart-py": Pinecone.Index(...),
                "another-index": Pinecone.Index(...),
                ...
              }

    Output: dict[str, dict[str, int]]
        - Nested dict: {index_name: {namespace: vector_count, ...}, ...}
        - example: {
            "developer-quickstart-py": {"test": 100, "prod": 200},
            "another-index": {"namespace1": 50},
            ...
          }
    """
    result = {}
    processed_pairs = set()  # Track processed (index_name, namespace) pairs

    for video_url, config_data in video_config.items():
        index_name = config_data.get("index_name")
        namespace = config_data.get("namespace")

        if not index_name or not namespace:
            print(f"Warning: Missing index_name or namespace for video {video_url}")
            continue

        # Skip if already processed
        pair = (index_name, namespace)
        if pair in processed_pairs:
            continue

        # Get pc_index object -> 처리해야 할 index인데 연결된 pc_index 객체가 없는 경우
        if index_name not in dict_of_pc_index:
            print(f"Warning: Index '{index_name}' not found in dict_of_pc_index")
            continue

        pc_index = dict_of_pc_index[index_name]

        # Get namespace length
        try:
            stats = pc_index.describe_index_stats()
            if namespace in stats.get("namespaces", {}):
                vector_count = stats["namespaces"][namespace]["vector_count"]
            else:
                vector_count = 0

            # Store result
            if index_name not in result:
                result[index_name] = {}
            result[index_name][namespace] = vector_count

            # Mark as processed
            processed_pairs.add(pair)

        except Exception as e:
            print(f"Error getting namespace length for {index_name}/{namespace}: {e}")
            continue

    return result

# === Data transformation to vectorDB data format ===

def transcript_to_record(id:str, transcript_data:dict, field_map:dict, Author:str="", Comment:str="") -> dict:
    """
    Convert transcript data to record
    Input: transcript_data, field_map
        - transcript_data: dict type
            - example: {"text": "Hello, world!", "start": 0.12, "end": 3.72, "title":'Guide_of_LLM', "channelTitle":'Test_channel', "publishedAt":'2025-02-05T18:23:47Z'},
        - field_map: dict type
            - example: {"text": "chunk_text"}

    Output: list[dict] type
        - example: {"id": "rec1", "chunk_text": "Hello, world!", metadata: str({"start": 0.12, "end": 3.72, "title":'Guide_of_LLM', "channelTitle":'Test_channel', "publishedAt":'2025-02-05T18:23:47Z'})}
    """
    if Author == "" and Comment == "":
        result = {
            "id": str(id),
            f"{field_map['text']}": transcript_data["text"],
            "metadata": str(
                    {
                    "start": transcript_data["start"],
                    "end": transcript_data["end"],
                    "title": transcript_data["title"],
                    }
                )
            }
    else:
        result = {
            "id": str(id),
            f"{field_map['text']}": transcript_data["text"],
            "metadata": str(
                    {
                    "start": transcript_data["start"],
                    "end": transcript_data["end"],
                    "title": transcript_data["title"],
                    "Author": Author,
                    "Comment": Comment
                    }
                )
            }
    return result

def transcript_to_record_batch(video_ids:str, transcript_data:list[dict], dict_of_pc_index:dict[str, "Pinecone.Index"], video_config:dict) -> list[dict]:
    """
    Convert transcript data to record
    Input: video_ids, transcript_data, dict_of_pc_index, video_config
        - video_ids: list[str] type
            - example: ["video_id1", "video_id2", ...]
        - transcript_data: list[dict] type
            - example: [
                        {"text": "Hello, world!", "start": 0.12, "end": 3.72, "title":'Guide_of_LLM', "channelTitle":'Test_channel', "publishedAt":'2025-02-05T18:23:47Z'},
                        {"text": "How are you?", "start": 3.73, "end": 5.61, "title":'Guide_of_LLM', "channelTitle":'Test_channel', "publishedAt":'2025-02-05T18:23:47Z'},
                        ...
                        ]
        - dict_of_pc_index: dict[str, Pinecone.Index(host=PINECONE_HOST)]
        - video_config: dict with video URLs as keys and config dicts as values

    Output: list[dict] type
        - example: [
                {"id": "rec1", "chunk_text": "Hello, world!", metadata: str({"start": 0.12, "end": 3.72, "title":'Guide_of_LLM', "channelTitle":'Test_channel', "publishedAt":'2025-02-05T18:23:47Z'})}
                {"id": "rec2", "chunk_text": "How are you?", metadata: str({"start": 3.73, "end": 5.61, "title":'Guide_of_LLM', "channelTitle":'Test_channel', "publishedAt":'2025-02-05T18:23:47Z'})}
                ...
            ]
    """
    # Get namespace lengths for all index-namespace pairs
    namespace_len_dict = get_namespace_len(video_config=video_config, dict_of_pc_index=dict_of_pc_index)
    """
    namespace_len_dict == {
        "developer-quickstart-py": {"test": 100, "prod": 200},
        "another-index": {"namespace1": 50},
        ...
    }
    """

    # Track ID counter for each (index_name, namespace) pair
    id_trackers = {}  # {(index_name, namespace): current_id}

    # Initialize trackers with existing vector counts
    for index_name, namespaces in namespace_len_dict.items():
        for namespace, count in namespaces.items():
            id_trackers[(index_name, namespace)] = count + 1

    result = {}
    for video_id in video_ids:
        result[video_id] = []
        # Find the video's config by matching video_id with video URLs in video_config
        video_url = None
        for url in video_config.keys():
            if video_id == extract_video_id(url):  # video_id is extracted from URL
                video_url = url
                break

        if not video_url:
            print(f"Warning: Could not find config for video_id {video_id}")
            continue

        config_data = video_config[video_url]
        index_name = config_data.get("index_name")
        namespace = config_data.get("namespace")
        field_map = config_data.get("embed", {}).get("field_map", {"text": "chunk_text"})
        author = config_data.get("Author", "")
        comment = config_data.get("Comment", "")

        if not index_name or not namespace:
            print(f"Warning: Missing index_name or namespace for video {video_id}")
            continue

        # Get current ID for this index-namespace pair
        pair = (index_name, namespace)
        if pair not in id_trackers:
            id_trackers[pair] = 1  # Start from 1 if not found

        id_start = id_trackers[pair]

        print(f"Processing video {video_id} in {index_name}/{namespace}, starting from ID {id_start}")

        for id, record in enumerate(transcript_data[video_id], id_start):
            result[video_id].append(transcript_to_record(id=f"{video_id}__{id}", transcript_data=record, field_map=field_map, Author=author, Comment=comment))
            id_trackers[pair] += 1  # Increment counter for this index-namespace

    return result



def main():
    # === Data processing ===
    global INPUT_FILE_PATH, INPUT_FILE_NAME, INPUT_FILE_EXTENSION
    global OUTPUT_FILE_PATH, OUTPUT_FILE_NAME, OUTPUT_FILE_EXTENSION
    global PINECONE_API_KEY

    # Load video config from YAML
    video_config = load_video_config()

    # Connect to Pinecone and get index-host mapping
    pc = connect_to_Pinecone(api_key=PINECONE_API_KEY)
    index_host_mapping:dict[str, str] = get_index_host_mapping(pc)
    """
    index_host_mapping == {
        "developer-quickstart-py": "developer-quickstart-py-nibcub6.svc.aped-4627-b74a.pinecone.io",
        "another-index": "another-index-xyz123.svc.aped-4627-b74a.pinecone.io"
    }
    """

    # Create pc_index objects for each index
    dict_of_pc_index = {}
    for index_name, host in index_host_mapping.items():
        dict_of_pc_index[index_name]:dict[str, "Pinecone.Index"] = connect_to_Index(pc=pc, host=host)
    """
    dict_of_pc_index == {
        "developer-quickstart-py": Pinecone.Index(host="developer-quickstart-py-nibcub6.svc.aped-4627-b74a.pinecone.io"),
        "another-index": Pinecone.Index(host="another-index-xyz123.svc.aped-4627-b74a.pinecone.io")
    }
    """

    raw_transcript:dict[str, dict[str]] = file_loader(file_path=INPUT_FILE_PATH, file_name=INPUT_FILE_NAME, file_extension=INPUT_FILE_EXTENSION)
    previous_processed_video:dict[str, dict[str]] = file_loader(file_path=OUTPUT_FILE_PATH, file_name=OUTPUT_FILE_NAME, file_extension=OUTPUT_FILE_EXTENSION)
    if previous_processed_video is None:
        previous_processed_video:dict[str, dict[str]] = {}

    filtered_transcript:dict[str, dict[str]] = {}
    for youtube_id in raw_transcript.keys():
        if youtube_id not in list(previous_processed_video.keys()):
            filtered_transcript[youtube_id] = raw_transcript[youtube_id]
        else:
            pass

    current_result = sentence_by_SaT_with_metadata(filtered_transcript, model=config["SaT_model"], threshold=config["SaT_threshold"], concat_length=config["concat_length"], use_gpu=config["use_gpu"])
    data_processed_result = previous_processed_video.copy()
    data_processed_result.update(current_result)
    print("previous processed video: ", len(list(previous_processed_video.keys())))
    print("new processed video: ", len(list(filtered_transcript.keys())))
    save_result_to_file(result=data_processed_result, file_path=OUTPUT_FILE_PATH, file_name=OUTPUT_FILE_NAME, file_extension=OUTPUT_FILE_EXTENSION)
    
    # === Data transformation to vectorDB data format ===
    vectorDB_data_processed_result = transcript_to_record_batch(
        video_ids=list(data_processed_result.keys()), 
        transcript_data=data_processed_result, 
        dict_of_pc_index=dict_of_pc_index, 
        video_config=video_config
    )
    save_result_to_file(result=vectorDB_data_processed_result, file_path=OUTPUT_FILE_PATH, file_name="vectorDB_upsert_data", file_extension="json")

    return vectorDB_data_processed_result

if __name__ == "__main__":
    vectorDB_data_processed_result = main()
    print("Done!")