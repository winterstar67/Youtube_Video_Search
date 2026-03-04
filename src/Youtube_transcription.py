"""
oreder in pipeline: First (1)
    - Next_file: transcript_processing.py

youtube_transcript_api를 사용하여 지정한 동영상들의 자막을 추출하는 모듈

Input: 
    - File directory: data/raw_data/video_link_target.yaml
        - Key: target_video_link
        - Value: list of video links
    - {"video_link_target": ["https://www.youtube.com/watch?v=EWvNQjAaOHw", "https://www.youtube.com/watch?v=7xTGNNLPyMI"]}

Output:
    - File directory: data/
        - Key: each_video_link
        - Value: transcription of each video
    - {"each_video_link": "transcription of each video"}

Feature:
    - 기존에 있는 자막이 있는 경우, 기존 자막을 유지하고 새로운 자막을 추가하는 기능 추가

Todo list:
    - 나중에 동영상 개수가 많아지게 되는 경우, result dictionary에서 key에 인물 혹은 채널 key를 추가하여 level을 하나 더 만들어서 관리하도록 수정하자.


잡 생각:
    - VectorDB에서 쓸모없는 문장을 없앴을 때 장점:
        - Vector DB에 쓸데없는 데이터가 줄어들어서 공간도 절약하고, searching time도 줄어든다.

"""
from youtube_transcript_api import YouTubeTranscriptApi
import gpt_based_weired_word_sensor
from Youtube_tool.ID_extraction import extract_video_id
from Youtube_tool import Youtube_Collection
import os
import yaml
import pickle
import pandas as pd
from datetime import datetime

# ================================ File path configuration ================================
current_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.dirname(current_path)

import sys
sys.path.append(parent_path)
from utils import file_path_reader
from utils.file_path_reader import file_loader, save_result_to_file, concat_data

INPUT_FILE_PATH:str = os.path.join(parent_path, "data", "raw_data")
INPUT_FILE_NAME:str = "video_link_target"
INPUT_FilE_EXTENSION:str = "yaml"


SCRIPT_NAME:str = os.path.splitext(os.path.basename(__file__))[0]  # "Youtube_transcription"
OUTPUT_FILE_PATH:str = os.path.join(parent_path, "data", "results", SCRIPT_NAME)
OUTPUT_FILE_NAME:str = "Youtube_transcription"
OUTPUT_FILE_EXTENSION:str = "pkl"

# ================================ Function definition ================================
def check_input_file_existence() -> None:
    """
    Check if the input file exists
    """
    global INPUT_FILE_PATH, INPUT_FILE_NAME
    INPUT_FILE_PATH_WITH_NAME = os.path.join(INPUT_FILE_PATH, INPUT_FILE_NAME)

    try:
        if not os.path.exists(INPUT_FILE_PATH_WITH_NAME):
            raise FileNotFoundError(f"File not found: {INPUT_FILE_PATH_WITH_NAME}")
        else:
            print("Input file already exists")
    except Exception as e:
        print("Error at check_input_file_existence: " + str(e))

def check_result_path_existence() -> None:
    """
    Check if the result save path exists
    """
    global OUTPUT_FILE_PATH

    try:
        if not os.path.exists(OUTPUT_FILE_PATH):
            os.makedirs(OUTPUT_FILE_PATH, exist_ok=True)
        else:
            print("Result save path already exists")
        
        if not os.path.exists("backup"):
            os.makedirs("backup", exist_ok=True)
        else:
            print("Backup file path already exists")
    except Exception as e:
        print("Error at check_result_path_existence: " + str(e))

def get_transcription(file_path:str=None) -> dict[str, list[dict]]:
    """
    Get transcription of each video using YouTubeTranscriptApi

    Args:
        file_path (str, optional): Path to YAML file containing YouTube video links.
            Defaults to INPUT_FILE_PATH/INPUT_FILE_NAME ("data/raw_data/video_link_target.yaml")

    Returns:
        dict[str, FetchedTranscript]: Dictionary mapping video URL to transcript object
            Key: YouTube video URL (str)
                Example: "https://www.youtube.com/watch?v=EWvNQjAaOHw"
            Value: FetchedTranscript object with following attributes:
                - video_id (str): YouTube video ID extracted from URL
                - language (str): Full language name (e.g., "English (auto-generated)")
                - language_code (str): ISO language code (e.g., "en")
                - is_generated (bool): Whether transcript is auto-generated
                - snippets (list[FetchedTranscriptSnippet]): List of transcript segments
                    Each FetchedTranscriptSnippet contains:
                        - text (str): Transcript text content
                        - start (float): Start time in seconds
                        - duration (float): Duration in seconds

    Side Effects:
        - Saves results to "data/results/Youtube_transcription.pkl"
        - Creates backup in "backup/Youtube_transcription_YYYYMMDD.pkl"
        - Prints messages for already-processed videos

    Example:
        >>> result = get_transcription()
        >>> first_url = list(result.keys())[0]
        >>> transcript = result[first_url]
        >>> print(transcript.video_id)  # 'EWvNQjAaOHw'
        >>> print(transcript.language)  # 'English (auto-generated)'
        >>> print(len(transcript.snippets))  # 3475
        >>> first_snippet = transcript.snippets[0]
        >>> print(first_snippet.text)  # 'hi everyone so in this video I would'
        >>> print(first_snippet.start)  # 0.12
        >>> print(first_snippet.duration)  # 3.72
    """
    global OUTPUT_FILE_PATH, OUTPUT_FILE_NAME, OUTPUT_FILE_EXTENSION
    global INPUT_FILE_PATH, INPUT_FILE_NAME, INPUT_FilE_EXTENSION
    
    try:
        # 이전에 처리했던 결과 데이터 로드
        youtube_transcription_dict_loaded:dict[str, list[dict]] = file_loader(file_path=OUTPUT_FILE_PATH, file_name=OUTPUT_FILE_NAME, file_extension=OUTPUT_FILE_EXTENSION)
        if youtube_transcription_dict_loaded is None: # 파일이 없는 경우
            youtube_transcription_dict_loaded:dict = {}

        # 현재 처리하고자 하는 모든 데이터, 단 이전에 처리했던 내용을 실수로 지우지 않은 경우, 중복되어 있을 수 있음. 그래서 아래에서 후처리로 중복된 비디오는 skip 작업을 진행하는 것
        all_link_lists:list[str] = list(file_loader(file_path=INPUT_FILE_PATH, file_name=INPUT_FILE_NAME, file_extension=INPUT_FilE_EXTENSION).keys())
        target_video_lists:list[str] = []

        # 처리하려는 영상 리스트 중에서 과거에 이미 처리되어 VectorDB에 저장된 경우는 skip하기 위해, 과거 데이터에 없는 데이터만 유튜브 처리 대상으로 추가하는 과정
        for video_link in all_link_lists:
            youtube_id = extract_video_id(video_link)
            if youtube_id not in list(youtube_transcription_dict_loaded.keys()):
                target_video_lists.append(youtube_id)
            else:
                print(f"Transcription already exists: {video_link}")
        
        print("3")
        # 이제 유튜브 처리 대상으로 선별된 데이터에 대해서만 지막을 수집해서 {youtube_id: FetchedTranscript} 형태의 dictionary를 생성하는 과정
        youtube_transcription_dict = {}
        for youtube_id in target_video_lists:
            ytt_api:YouTubeTranscriptApi = YouTubeTranscriptApi()
            youtube_transcription_dict[youtube_id] = ytt_api.fetch(youtube_id)
        print("Youtube transcription is fetched")

        # 유튜브 처리 대상으로 선별된 데이터에 대해서 유튜브 정보를 수집하는 과정
            # 동영상 제목
            # 동영상 채널 제목
            # 동영상 설명
            # 동영상 썸네일
            # 등등
        youtube_video_infos:dict = Youtube_Collection.main()
        value_sample = youtube_video_infos[list(youtube_video_infos.keys())[0]]
        columns = ['youtube_id', *list(value_sample.keys())]
        try:
            prev_youtube_video_infos_df = file_loader(file_path=OUTPUT_FILE_PATH, file_name="ID_Table", file_extension="csv")
        except Exception as e:
            print("Error at prev_youtube_video_infos_df: " + str(e))
            prev_youtube_video_infos_df = pd.DataFrame(columns=columns)
        youtube_video_infos_df = pd.DataFrame.from_dict(youtube_video_infos, orient='index').reset_index().rename(columns={'index': 'youtube_id'})
        result_df = concat_data(prev_youtube_video_infos_df, youtube_video_infos_df, 'csv')
        save_result_to_file(result_df, file_path=OUTPUT_FILE_PATH, file_name="ID_Table", file_extension="csv")
        print("Youtube video infos are fetched")

        # 유튜브 처리 대상으로 선별된 데이터에 대해서 유튜브 정보와 유튜브 자막 텍스트를 합치는 과정
        merged_dict = {
            key: {"transcription":youtube_transcription_dict[key], "video_info":youtube_video_infos[key]}
            for key in youtube_transcription_dict.keys()
        }

        # 과거 데이터와 새로운 데이터를 합치는 과정
        result = concat_data(youtube_transcription_dict_loaded, merged_dict, 'json')
        print("Merged dictionary is created")
        save_result_to_file(merged_dict, file_path=OUTPUT_FILE_PATH, file_name=OUTPUT_FILE_NAME, file_extension=OUTPUT_FILE_EXTENSION)
        save_result_to_file(result, file_path=OUTPUT_FILE_PATH, file_name=OUTPUT_FILE_NAME+"_stacked_version", file_extension=OUTPUT_FILE_EXTENSION)

        gpt_based_weired_word_sensor.main()

        return result
    
    except Exception as e:
        print("Error at get_transcription: " + str(e))
        return {}

if __name__ == "__main__":
    try:
        result:dict[str, list[dict]] = get_transcription()
        
    except Exception as e:
        print(str(e) + f"at file: {__file__}")
    
