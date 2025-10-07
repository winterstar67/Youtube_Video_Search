"""
oreder in pipeline: First (1)
    - Next_file: transcript_processing.py

youtube_transcript_api를 사용하여 지정한 동영상들의 자막을 추출하는 모듈

Input: 
    - File directory: data/external_data/video_link_target.yaml
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

INPUT_FILE_PATH:str = os.path.join(parent_path, "data", "external_data")
INPUT_FILE_NAME:str = "video_link_target.yaml"

OUTPUT_FILE_PATH:str = os.path.join(parent_path, "data", "results")
OUTPUT_FILE_EXTENSION:str = "pkl"
OUTPUT_FILE_NAME:str = "Youtube_transcription"

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

def output_dictionary_loader(output_file_path:str, output_file_name:str, output_file_extension:str) -> dict[str, list[dict]]:
    """
    Load output dictionary from pickle file

    Input: output_file_path, output_file_name, output_file_extension
        - example: "data/results", "Youtube_transcription", "pkl"

    Output: dict[str, list[dict]]
    """
    output_file_path_with_name = output_file_path + "/" + output_file_name + "." + output_file_extension
    try:
        if not os.path.exists(output_file_path_with_name):
            return {}
        else:
            with open(output_file_path_with_name, "rb") as f:
                return pickle.load(f)
    except Exception as e:
        print("Error at output_dictionary_loader: " + str(e))
        return {}

def save_result_to_file(youtube_transcription_dict:dict[str, list[dict]], output_file_path:str, output_file_name:str, output_file_extension:str) -> None:
    """
    Save result to file
    """
    backup_file_path = file_path_reader.backup_file_path_reader(output_file_name=output_file_name, output_file_extension=output_file_extension)

    try:
        with open(output_file_path + "/" + output_file_name + "." + output_file_extension, "wb") as f:
            pickle.dump(youtube_transcription_dict, f)    

        with open(backup_file_path, "wb") as f:
            pickle.dump(youtube_transcription_dict, f)

    except Exception as e:
        print("Error at save_result_to_file: " + str(e))

def save_result_to_csv(youtube_video_infos:dict[str, list[dict]], output_file_path:str, output_file_name:str, output_file_extension:str) -> None:
    """
    Save result to csv file
    It save ID Table to csv file
    Input: youtube_video_infos
    Output: None
    - type: dict[str, list[dict]]
    - example:
      {
        'youtube_id': {
          'title': 'title',
          'channelTitle': 'channelTitle',
          'description': 'description',
          'publishedAt': 'publishedAt',
          'channelId': 'channelId',
          'defaultLanguage': 'defaultLanguage',
          'categoryId': 'categoryId'
        }
      }

    Output: None
    """
    backup_file_path = file_path_reader.backup_file_path_reader(output_file_name=output_file_name, output_file_extension=output_file_extension)
    value_sample = youtube_video_infos[list(youtube_video_infos.keys())[0]]
    columns = ['youtube_id', *list(value_sample.keys())]
    try:
        if os.path.exists(output_file_path + "/" + output_file_name + ".csv"):
            previous_output_df = pd.read_csv(OUTPUT_FILE_PATH + OUTPUT_FILE_NAME + ".csv")
        else:
            previous_output_df = pd.DataFrame(columns=columns)
        
        current_output_df = pd.DataFrame.from_dict(youtube_video_infos, orient='index').reset_index()
        current_output_df = current_output_df.rename(columns={'index': 'youtube_id'})

        output_df = pd.concat([previous_output_df, current_output_df], ignore_index=True)
        output_df.to_csv(output_file_path + "/" + output_file_name + ".csv", index=False)
        
        backup_df = pd.concat([previous_output_df, current_output_df], ignore_index=True)
        backup_df.to_csv(backup_file_path, index=False)

    except Exception as e:
        print("Error at save_result_to_csv: " + str(e))


def get_transcription(file_path:str=None) -> dict[str, list[dict]]:
    """
    Get transcription of each video using YouTubeTranscriptApi

    Args:
        file_path (str, optional): Path to YAML file containing YouTube video links.
            Defaults to INPUT_FILE_PATH/INPUT_FILE_NAME ("data/external_data/video_link_target.yaml")

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
    global INPUT_FILE_PATH, INPUT_FILE_NAME

    try:
        if file_path is None:
            file_path = os.path.join(INPUT_FILE_PATH, INPUT_FILE_NAME)

        check_result_path_existence()
        check_input_file_existence()

        youtube_transcription_dict_loaded:dict[str, list[dict]] = output_dictionary_loader(output_file_path=OUTPUT_FILE_PATH, output_file_name=OUTPUT_FILE_NAME, output_file_extension=OUTPUT_FILE_EXTENSION)

        with open(file_path, "r", encoding="utf-8") as f:
            _target_link_lists:list[str] = yaml.safe_load(f)['target_video_link']
        
        youtube_id_list:list[str] = []
        for target_link in _target_link_lists:
            youtube_id = extract_video_id(target_link)
            if youtube_id not in list(youtube_transcription_dict_loaded.keys()):
                youtube_id_list.append(youtube_id)
            else:
                print(f"Transcription already exists: {target_link}")

        youtube_transcription_dict = {}
        for youtube_id in youtube_id_list:
            ytt_api:YouTubeTranscriptApi = YouTubeTranscriptApi()
            youtube_transcription_dict[youtube_id] = ytt_api.fetch(youtube_id)
        print("Youtube transcription is fetched")

        youtube_video_infos:dict = Youtube_Collection.main()
        save_result_to_csv(youtube_video_infos, output_file_path=OUTPUT_FILE_PATH, output_file_name=OUTPUT_FILE_NAME, output_file_extension=OUTPUT_FILE_EXTENSION)
        print("Youtube video infos are fetched")

        merged_dict = {
            key: {"transcription":youtube_transcription_dict[key], "video_info":youtube_video_infos[key]}
            for key in youtube_transcription_dict.keys()
        }

        youtube_transcription_dict_loaded.update(merged_dict)
        print("Merged dictionary is created")

        result = youtube_transcription_dict_loaded

        save_result_to_file(result, output_file_path=OUTPUT_FILE_PATH, output_file_name=OUTPUT_FILE_NAME, output_file_extension=OUTPUT_FILE_EXTENSION)

        return result
    
    except Exception as e:
        print("Error at get_transcription: " + str(e))
        return {}

if __name__ == "__main__":
    try:
        result:dict[str, list[dict]] = get_transcription()
        
    except Exception as e:
        print(str(e) + f"at file: {__file__}")
    
