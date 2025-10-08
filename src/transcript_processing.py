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
from utils import file_path_reader


INPUT_FILE_PATH:str = os.path.join(parent_dir, "data", "results")
INPUT_FILE_NAME:str = "Youtube_transcription.pkl"
INPUT_FILE_EXTENSION:str = "pkl"
INPUT_FILE_PATH_WITH_NAME:str = os.path.join(INPUT_FILE_PATH, INPUT_FILE_NAME + "." + INPUT_FILE_EXTENSION)

OUTPUT_FILE_PATH:str = os.path.join(parent_dir, "data", "results")
OUTPUT_FILE_NAME:str = f"transcript_by_sentence"
OUTPUT_FILE_EXTENSION:str = "json"

config = {
    "PINECONE_API_KEY": os.getenv("PINECONE_API_KEY"),
    "PINECONE_HOST": os.getenv("PINECONE_HOST"),
    "SaT_model": "sat-1l-sm",
    "SaT_threshold": 0.35,
    "concat_length": 3,
    "use_gpu": False,
    "index_name": "developer-quickstart-py",
    "namespace": "test",
    "cloud": "aws",
    "region": "us-east-1",
    "embed": {
        "model":"llama-text-embed-v2",
        "field_map":{"text": "chunk_text"}
    }
}

def input_file_loader(input_file_path:str=INPUT_FILE_PATH, INPUT_FILE_NAME:str=INPUT_FILE_NAME, input_file_extension:str=INPUT_FILE_EXTENSION) -> dict:
    """
    Load input file

    Input: input_file_path type
        - example: "../data/results/transcript_by_sentence.json"

    Output: dict[str, list[dict]] type
        - example:
          {
            "EWvNQjAaOHw": {
                "transcription": [
                FetchedTranscript(snippets=[FetchedTranscriptSnippet(text='hi everyone so in this video I would', start=0.12, duration=3.72), 
                FetchedTranscriptSnippet(text='like to continue our general audience', start=2.159, duration=5.041), 
                ...
                ],
                "video_info": {
                    "title": "title",
                    "channelTitle": "channelTitle",
                    "description": "description",
                    "publishedAt": "publishedAt",
                    "channelId": "channelId",
                    "defaultLanguage": "defaultLanguage",
                    "categoryId": "categoryId"
                }
            },
            "7xTGNNLPyMI": {
                "transcription": [
                ...
                ],
                "video_info": {
                    ...
                }
            }
          }
    """
    input_file_path_with_name = input_file_path + "/" + input_file_name + "." + input_file_extension
    if input_file_extension == "json":
        with open(input_file_path_with_name, "r") as f:
            result = json.load(f)
    else:
        with open(input_file_path_with_name, "rb") as f:
            result = pickle.load(f)
    return result

def output_file_loader(output_file_path:str, output_file_name:str, output_file_extension:str) -> dict[str, list[dict]]:
    """
    Load output file
    이미 처리된 video가 있다면, 해당 경우는 제외하기 위한 목적으로 output file을 불러옴

    Input: output_file_path type
        - example: "data/results/transcript_by_sentence.json"

    Output: dict[str, list[dict]] type
        - example:
          {
            "EWvNQjAaOHw": [
                {text: 'hi everyone so in this video I would', start: 0.12, duration: 3.72}, 
                {text: 'like to continue our general audience', start: 2.159, duration: 5.041}, 
                {text: 'series on large language models like', start: 3.84, duration: 5.839},
                ...
            ]
          }
    """
    output_file_path_with_name = output_file_path + "/" + output_file_name + "." + output_file_extension
    if os.path.exists(output_file_path_with_name):
        with open(output_file_path_with_name, "r") as f:
            result = json.load(f)
    else:
        result = {}
    return result

def save_result_to_file(result:dict[str, list[dict]], file_path:str, file_name:str, file_extension:str) -> None:
    """
    Save result to file
    """
    backup_file_path = file_path_reader.backup_file_path_reader(output_file_name=file_name, output_file_extension=file_extension)
    if file_extension == "json":
        with open(file_path + "/" + file_name + "." + file_extension, "w") as f:
            json.dump(result, f)
        with open(backup_file_path, "w") as f:
            json.dump(result, f)
    else:
        with open(file_path + "/" + file_name + "." + file_extension, "wb") as f:
            pickle.dump(result, f)
        with open(backup_file_path, "wb") as f:
            pickle.dump(result, f)

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

def concatenate_with_neighbors_detailed(sentences:list[str], separator:str=' ', concat_length:int=3) -> list[str]:
    """
    리스트의 각 요소를 앞뒤 요소와 연결하는 함수 (구분자 옵션 포함)
    
    Parameters:
    -----------
    sentences : list[str],
        문장들의 리스트
    separator : str
        요소들 사이에 넣을 구분자 (기본값: 공백 ' ')
    concat_length : int
        연결할 요소의 개수 (기본값: 3)
        - 반드시 odd number로 설정해야 함.

    Returns:
    --------
    list[str]
        각 연결 결과를 포함한 리스트
        - 'index': 원본 리스트에서 중심 요소의 인덱스
        - 'previous': 앞 요소
        - 'current': 현재 요소
        - 'next': 뒤 요소
        - 'concatenated': 3개를 연결한 결과
    """
    if concat_length % 2 == 0:
        raise ValueError("concat_length must be an odd number")
    
    if len(sentences) < concat_length:
        return []
    
    results = []
    
    for i in range(concat_length//2, len(sentences) - concat_length//2):
        result = {
            'index': i,
            'previous': sentences[i-concat_length//2:i],
            'current': sentences[i],
            'next': sentences[i+1:i+concat_length//2+1],
            'concatenated': separator.join(sentences[i-concat_length//2 : i+concat_length//2+1])
        }
        results.append(result)
    
    return results

def text_list_preprocessing(text_list:list[str], concat_length:int) -> list[str]:
    """
    Preprocess text list
    Input: text_list type
        - example: ["hi everyone so I've wanted to make this video for a while", "it is a comprehensive", ...]
    Output: list[str] type
        - example: ["hi everyone so I've wanted to make this video for a while", "it is a comprehensive", ...]
    """
    filtering_short_text = text_pattern_filter.remove_filler_words(text=text_list)
    filtering_short_text = text_pattern_filter.remove_short_text(text_list=filtering_short_text, min_length=10)
    concatenated_text_by_SaT = concatenate_with_neighbors_detailed(sentences=filtering_short_text, separator=' ', concat_length=concat_length) # ["hi everyone so I've wanted to make this video for a while it is a comprehensive", ...]

    return concatenated_text_by_SaT

def attach_start_end(concatenated_text_by_SaT:list[str], youtube_transcripts_data:dict[str, dict[str]]) -> list[str]:
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

    for _sentence in concatenated_text_by_SaT: # Each sentence in one video
        sentence = _sentence['concatenated'] # 앞 뒤 setence를 concat함에 따라 concatenated_text_by_SaT의 'text'는 previous, current, next, concatenated를 가지고 있음. 여기서 필요한 것은 concatenated임.
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
                    "start":start_at_sentence, 
                    "end":round(end_at_sentence,3), 
                    "title":youtube_transcripts_data['video_info']['title'],
                    "channelTitle":youtube_transcripts_data['video_info']['channelTitle'],
                    "publishedAt":youtube_transcripts_data['video_info']['publishedAt']
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

        # start end를 붙이는 작업을 하기 전에 짧은 텍스트 쳐내기, 의미없는 text pattern filter 적용 등의 전처리하는 모듈이 필요하다.        
        segmented_text_by_SaT = text_list_preprocessing(segmented_text_by_SaT, concat_length=concat_length)
        sents_with_metadata = attach_start_end(concatenated_text_by_SaT=segmented_text_by_SaT, youtube_transcripts_data=youtube_transcripts_data)

        result[youtube_id] = sents_with_metadata

    save_result_to_file(result=full_text_dict, file_path=OUTPUT_FILE_PATH, file_name="Full_text__input_of_weired_wrd_sensor", file_extension="json")
    return result

# === namespace length function===
def get_namespace_len(pc_index:"Pinecone.Index", namespace:str=config["namespace"]) -> int: # Level 3 (namespace Level)
    """
    Get namespace length
    Input: pc_index, namespace
        - pc_index: Pinecone.Index(host=PINECONE_HOST)
        - namespace: "namespace"
    
    Output: int type
        - example: 2
    """
    exist = bool(pc_index.describe_index_stats()["namespaces"])
    if exist:
        return pc_index.describe_index_stats()["namespaces"][namespace]["vector_count"]
    else:
        return 0

# === Data transformation to vectorDB data format ===

# === Connect to VectorDB ===
def connect_to_Pinecone(api_key:str) -> Pinecone: # Level 1 (Pinecone Level)
    """
    Input: api_key type
        - example: PINECONE_API_KEY

    Output: Pinecone type
        - example: Pinecone(api_key=PINECONE_API_KEY)
    """
    return Pinecone(api_key=api_key)

def connect_to_Index(pc:Pinecone, host:str) -> "Pinecone.Index": # Level 2 (Index Level)
    """
    Connect to Index
    Input: pc, host
        - pc: Pinecone(api_key=PINECONE_API_KEY)
        - host: str type
            - example: PINECONE_HOST

    Output: Pinecone.Index type
        - example: Pinecone.Index(host=PINECONE_HOST)
    """
    return pc.Index(host=host)

def transcript_to_record(id:str, transcript_data:dict) -> dict:
    """
    Convert transcript data to record
    Input: transcript_data
        - transcript_data: dict type
            - example: {"text": "Hello, world!", "start": 0.12, "end": 3.72, "title":'Guide_of_LLM', "channelTitle":'Test_channel', "publishedAt":'2025-02-05T18:23:47Z'},

    Output: list[dict] type
        - example: {"id": "rec1", "text": "Hello, world!", metadata: str({"start": 0.12, "end": 3.72, "title":'Guide_of_LLM', "channelTitle":'Test_channel', "publishedAt":'2025-02-05T18:23:47Z'})}
    """
    result = {
        "id": str(id),
        f"{config["embed"]["field_map"]['text']}": transcript_data["text"],
        "metadata": str(
                {
                "start": transcript_data["start"],
                "end": transcript_data["end"]
                }
            )
        }
    return result

def transcript_to_record_batch(video_ids:str, transcript_data:list[dict], pc_index:"Pinecone.Index", namespace:str) -> list[dict]:
    """
    Convert transcript data to record
    Input: video_ids, transcript_data, pc_index, namespace
        - video_ids: list[str] type
            - example: ["video_id1", "video_id2", ...]
        - transcript_data: list[dict] type
            - example: [
                        {"text": "Hello, world!", "start": 0.12, "end": 3.72, "title":'Guide_of_LLM', "channelTitle":'Test_channel', "publishedAt":'2025-02-05T18:23:47Z'},
                        {"text": "How are you?", "start": 3.73, "end": 5.61, "title":'Guide_of_LLM', "channelTitle":'Test_channel', "publishedAt":'2025-02-05T18:23:47Z'},
                        ...
                        ]
        - pc_index: Pinecone.Index(host=PINECONE_HOST)
        - namespace: "namespace"

    Output: list[dict] type
        - example: [
                {"id": "rec1", "chunk_text": "Hello, world!", metadata: str({"start": 0.12, "end": 3.72, "title":'Guide_of_LLM', "channelTitle":'Test_channel', "publishedAt":'2025-02-05T18:23:47Z'})}
                {"id": "rec2", "chunk_text": "How are you?", metadata: str({"start": 3.73, "end": 5.61, "title":'Guide_of_LLM', "channelTitle":'Test_channel', "publishedAt":'2025-02-05T18:23:47Z'})}
                ...
            ]
    """
    result = []
    id_start = get_namespace_len(pc_index=pc_index, namespace=namespace) + 1
    id_start_tracker = id_start
    for video_id in video_ids:
        id_start = id_start_tracker
        for id, record in enumerate(transcript_data[video_id], id_start):
            result.append(transcript_to_record(id=f"{video_id}__{id}", transcript_data=record))
            id_start_tracker += 1

    return result



def main():
    # === Data processing ===
    global INPUT_FILE_PATH, INPUT_FILE_NAME, INPUT_FILE_EXTENSION
    global OUTPUT_FILE_PATH, OUTPUT_FILE_NAME, OUTPUT_FILE_EXTENSION

    pc = connect_to_Pinecone(api_key=config["PINECONE_API_KEY"])
    pc_index = connect_to_Index(pc=pc, host=config["PINECONE_HOST"])

    raw_transcript:dict[str, dict[str]] = input_file_loader(input_file_path=INPUT_FILE_PATH, INPUT_FILE_NAME=INPUT_FILE_NAME, input_file_extension=INPUT_FILE_EXTENSION)
    previous_processed_video:dict[str, list[dict]] = output_file_loader(output_file_path=OUTPUT_FILE_PATH, output_file_name=OUTPUT_FILE_NAME, output_file_extension=OUTPUT_FILE_EXTENSION)

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
    save_result_to_file(result={"concat_length":config["concat_length"], "result":data_processed_result}, file_path=OUTPUT_FILE_PATH, file_name=OUTPUT_FILE_NAME, file_extension=OUTPUT_FILE_EXTENSION)
    
    # === Data transformation to vectorDB data format ===
    vectorDB_data_processed_result = transcript_to_record_batch(video_ids=list(data_processed_result.keys()), transcript_data=data_processed_result, pc_index=pc_index, namespace=config["namespace"])    
    save_result_to_file(result=vectorDB_data_processed_result, file_path=OUTPUT_FILE_PATH, file_name="vectorDB_upsert_data", file_extension="json")

    return vectorDB_data_processed_result

if __name__ == "__main__":
    vectorDB_data_processed_result = main()
    print("Done!")