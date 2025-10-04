"""
oreder in pipeline: First (1)

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
import os
import yaml
import pickle
from datetime import datetime

# ================================ File path configuration ================================
INPUT_FILE_PATH:str = "data/external_data"
INPUT_FILE_NAME:str = "video_link_target.yaml"

OUTPUT_FILE_PATH:str = "data/results"
OUTPUT_FILE_NAME:str = "Youtube_transcription.pkl"

BACKUP_FILE_PATH:str = f"backup/"
BACKUP_FILE_NAME:str = f"{OUTPUT_FILE_NAME}_{datetime.now().strftime('%Y%m%d')}.pkl"

# ================================ Function definition ================================
def check_input_file_existence() -> None:
    """
    Check if the input file exists
    """
    global INPUT_FILE_PATH, INPUT_FILE_NAME
    INPUT_FILE_PATH_with_name = os.path.join(INPUT_FILE_PATH, INPUT_FILE_NAME)

    if not os.path.exists(INPUT_FILE_PATH_with_name):
        raise FileNotFoundError(f"File not found: {INPUT_FILE_PATH_with_name}")
    else:
        print("Input file already exists")

def check_result_path_existence() -> None:
    """
    Check if the result save path exists
    """
    global OUTPUT_FILE_PATH, OUTPUT_FILE_NAME, BACKUP_FILE_PATH, BACKUP_FILE_NAME
    OUTPUT_FILE_PATH_with_name = os.path.join(OUTPUT_FILE_PATH, OUTPUT_FILE_NAME)
    BACKUP_FILE_PATH_with_name = os.path.join(BACKUP_FILE_PATH, BACKUP_FILE_NAME)

    if not os.path.exists(OUTPUT_FILE_PATH_with_name):
        os.makedirs(OUTPUT_FILE_PATH, exist_ok=True)
    else:
        print("Result save path already exists")
    
    if not os.path.exists(BACKUP_FILE_PATH_with_name):
        os.makedirs(BACKUP_FILE_PATH, exist_ok=True)
    else:
        print("Backup file path already exists")

def output_dictionary_loader() -> dict[str, list[dict]]:
    """
    Load output dictionary from pickle file
    """
    global OUTPUT_FILE_PATH, OUTPUT_FILE_NAME
    OUTPUT_FILE_PATH_with_name = os.path.join(OUTPUT_FILE_PATH, OUTPUT_FILE_NAME)

    if not os.path.exists(OUTPUT_FILE_PATH_with_name):
        return {}    
    else:
        with open(OUTPUT_FILE_PATH_with_name, "rb") as f:
            return pickle.load(f)

def save_result_to_file(youtube_transcription_dict:dict[str, list[dict]]) -> None:
    """
    Save result to file
    """
    global OUTPUT_FILE_PATH, OUTPUT_FILE_NAME, BACKUP_FILE_PATH, BACKUP_FILE_NAME
    OUTPUT_FILE_PATH_with_name = os.path.join(OUTPUT_FILE_PATH, OUTPUT_FILE_NAME)
    BACKUP_FILE_PATH_with_name = os.path.join(BACKUP_FILE_PATH, BACKUP_FILE_NAME)

    with open(OUTPUT_FILE_PATH_with_name, "wb") as f:
        pickle.dump(youtube_transcription_dict, f)    

    with open(BACKUP_FILE_PATH_with_name, "wb") as f:
        pickle.dump(youtube_transcription_dict, f)

def get_transcription(file_path:str=None, result_save_path:str=OUTPUT_FILE_PATH) -> dict[str, list[dict]]:
    """
    Get transcription of each video using YouTubeTranscriptApi

    Args:
        file_path (str, optional): Path to YAML file containing YouTube video links.
            Defaults to INPUT_FILE_PATH/INPUT_FILE_NAME ("data/external_data/video_link_target.yaml")
        result_save_path (str, optional): Directory path to save results.
            Defaults to OUTPUT_FILE_PATH ("data/results")

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
    global INPUT_FILE_PATH, INPUT_FILE_NAME, OUTPUT_FILE_PATH, OUTPUT_FILE_NAME, BACKUP_FILE_PATH, BACKUP_FILE_NAME

    if file_path is None:
        file_path = os.path.join(INPUT_FILE_PATH, INPUT_FILE_NAME)

    check_result_path_existence()
    check_input_file_existence()

    youtube_transcription_dict:dict[str, list[dict]] = output_dictionary_loader()

    with open(file_path, "r", encoding="utf-8") as f:
        _target_link_lists:list[str] = yaml.safe_load(f)['target_video_link']
    
    youtube_link_list:list[str] = []
    for target_link in _target_link_lists:
        if target_link not in list(youtube_transcription_dict.keys()):
            youtube_link_list.append(target_link)
        else:
            print(f"Transcription already exists: {target_link}")

    for youtube_link in youtube_link_list:
        video_id:str = extract_video_id(youtube_link)
        ytt_api:YouTubeTranscriptApi = YouTubeTranscriptApi()
        youtube_transcription_dict[youtube_link] = ytt_api.fetch(video_id)

    save_result_to_file(youtube_transcription_dict)

    return youtube_transcription_dict

if __name__ == "__main__":
    result:dict[str, list[dict]] = get_transcription()
    print(result)

