"""
oreder in pipeline: Second (2)

Function:
    1. 자막을 Youtube_transcription.py에서 받아와서, SaT를 사용하여 문장 단위로 모아서 다시 split를 함.
    2. 문장 단위로 split할 때, 각 문장마다 시작 시간과 종료 시간을 추가함.

Input: 
    - File directory: data/results/Youtube_transcription.pkl
        - Key: each_video_link
        - Value: transcription of each video
    - {"each_video_link": "transcription of each video"}
Output:
    - File directory: data/results/transcript_by_sentence.pkl
        - Key: each_video_link
        - Value: transcription of each video by sentence
    - {"each_video_link": "transcription of each video by sentence"}


Todo list:
    - SaT의 seg.split() 함수에서 threshold의 역할이 무엇인지 파악해야 함. 2025-10-05

transcript_processing.py
"""

import os
import pickle
from wtpsplit import SaT
from youtube_transcript_api import YouTubeTranscriptApi

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

INPUT_FILE_PATH:str = os.path.join(parent_dir, "data", "results")
INPUT_FILE_NAME:str = "Youtube_transcription.pkl"
INPUT_FILE_PATH_WITH_NAME:str = os.path.join(INPUT_FILE_PATH, INPUT_FILE_NAME)

OUTPUT_FILE_PATH:str = os.path.join(parent_dir, "data", "results")
OUTPUT_FILE_NAME:str = "transcript_by_sentence.pkl"
OUTPUT_FILE_PATH_WITH_NAME:str = os.path.join(OUTPUT_FILE_PATH, OUTPUT_FILE_NAME)

BACKUP_FILE_PATH:str = os.path.join(parent_dir, "backup")
BACKUP_FILE_NAME:str = "transcript_by_sentence_YYYYMMDD.pkl"
BACKUP_FILE_PATH_WITH_NAME:str = os.path.join(BACKUP_FILE_PATH, BACKUP_FILE_NAME)

config = {
    "SaT_model": "sat-1l-sm",
    "SaT_threshold": 0.35
}

def input_file_loader(input_file_path:str=INPUT_FILE_PATH_WITH_NAME) -> dict:
    """
    Load input file

    Input: input_file_path type
        - example: "data/results/Youtube_transcription.pkl"

    Output: dict[str, list[dict]] type
        - example:
          {
            "https://www.youtube.com/watch?v=EWvNQjAaOHw": [
                {"text": "hi everyone so I've wanted to make this video for a while", "start": 0.719, "end": 5.4},
                {"text": "it is a comprehensive", "start": 5.4, "end": 10.72},
                ...
            ]
          }
    """
    with open(input_file_path, "rb") as f:
        result = pickle.load(f)
    return result

def save_result_to_file(result:dict[str, list[dict]], file_path:str=OUTPUT_FILE_PATH_WITH_NAME, backup_file_path:str=BACKUP_FILE_PATH_WITH_NAME) -> None:
    """
    Save result to file
    """
    with open(file_path, "wb") as f:
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

def sentence_by_SaT(text:list[str], model:str=config["SaT_model"], threshold:float=config["SaT_threshold"]) -> list[str]:
    """
    Split text into sentences using SaT
    Input: text type
        - example: "hi everyone so I've wanted to make this video for a while it is a comprehensive"
    Output: list[str] type
        - example: ["hi everyone so I've wanted to make this video for a while", "it is a comprehensive", ...]
    """
    seg:list[str] = SaT(model)
    raw = seg.split(text, threshold=threshold)
    return raw


def sentence_by_SaT_with_metadata(model:str=config["SaT_model"], threshold:float=config["SaT_threshold"]) -> dict[str, list[dict]]:
    """
    Split text into sentences using SaT with metadata
    Input:
        - model example: "sat-1l-sm"
        - threshold example: 0.35
    Output: dict[str, list[dict]] type
        - example: 
          [
          {"text": "hi everyone so I've wanted to make this video for a while", "start": 0.719, "end": 5.4},
          {"text": "it is a comprehensive", "start": 5.4, "end": 10.72},
          ...
          ]
    """
    global INPUT_FILE_PATH_WITH_NAME, OUTPUT_FILE_PATH_WITH_NAME, BACKUP_FILE_PATH_WITH_NAME

    raw_transcript:dict[str, list[dict]] = input_file_loader(INPUT_FILE_PATH_WITH_NAME)
    
    result:dict[str, list[dict]] = {}

    for youtube_link, youtube_transcripts_data in raw_transcript.items(): # Each video
        Full_text:str = YouTubeTranscript_to_text(youtube_transcripts_data) # "hi everyone so I've wanted to make this video for a while it is a comprehensive"
        segmented_text_by_SaT = sentence_by_SaT(text=Full_text, model=model, threshold=threshold) # ["hi everyone so I've wanted to make this video for a while", "it is a comprehensive", ...]
        raw_index, sents_with_metadata = 0, [] # raw_index: 0, sents_with_metadata: [], initionalization

        for sentence in segmented_text_by_SaT: # Each sentence in one video
            raw_index_at_sentence, start_at_sentence = raw_index, 0 # raw_index_at_sentence: raw_index, start_at_sentence: 0, initionalization

            for raw_split_string in youtube_transcripts_data[raw_index_at_sentence:]: # Each split string in one video
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
                    sents_with_metadata.append({"text":sentence, "start":start_at_sentence, "end":round(end_at_sentence,3)})
                    break


        result[youtube_link] = sents_with_metadata

    save_result_to_file(result=result, file_path=OUTPUT_FILE_PATH_WITH_NAME, backup_file_path=BACKUP_FILE_PATH_WITH_NAME)

    return result

def main():
    result = sentence_by_SaT_with_metadata(model=config["SaT_model"], threshold=config["SaT_threshold"])
    return result


if __name__ == "__main__":
    result = main()
    print("Done!")