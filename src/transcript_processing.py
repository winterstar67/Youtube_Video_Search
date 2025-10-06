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
import json
from wtpsplit import SaT
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

INPUT_FILE_PATH:str = os.path.join(parent_dir, "data", "results")
INPUT_FILE_NAME:str = "Youtube_transcription.pkl"
INPUT_FILE_PATH_WITH_NAME:str = os.path.join(INPUT_FILE_PATH, INPUT_FILE_NAME)

OUTPUT_FILE_PATH:str = os.path.join(parent_dir, "data", "results")
OUTPUT_FILE_NAME:str = f"transcript_by_sentence"
OUTPUT_FILE_EXTENSION:str = "json"
OUTPUT_FILE_PATH_WITH_NAME:str = os.path.join(OUTPUT_FILE_PATH, OUTPUT_FILE_NAME) + "." + OUTPUT_FILE_EXTENSION

BACKUP_FILE_PATH:str = os.path.join(parent_dir, "backup")
BACKUP_FILE_NAME:str = f"{OUTPUT_FILE_NAME}_{datetime.now().strftime('%Y%m%d')}.{OUTPUT_FILE_EXTENSION}"
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
    with open(input_file_path, "rb") as f:
        result = pickle.load(f)
    return result

def output_file_loader(output_file_path:str=OUTPUT_FILE_PATH_WITH_NAME) -> dict[str, list[dict]]:
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
    if os.path.exists(output_file_path):
        with open(output_file_path, "r") as f:
            result = json.load(f)
    else:
        result = {}
    return result

def save_result_to_file(result:dict[str, list[dict]], file_path:str=OUTPUT_FILE_PATH_WITH_NAME, backup_file_path:str=BACKUP_FILE_PATH_WITH_NAME) -> None:
    """
    Save result to file
    """
    with open(file_path, "w") as f:
        json.dump(result, f)

    with open(backup_file_path, "w") as f:
        json.dump(result, f)

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

def concatenate_with_neighbors_detailed(sentences:list[str], separator:str=' ') -> list[str]:
    """
    리스트의 각 요소를 앞뒤 요소와 연결하는 함수 (구분자 옵션 포함)
    
    Parameters:
    -----------
    sentences : list[str]
        문장들의 리스트
    separator : str
        요소들 사이에 넣을 구분자 (기본값: 공백 ' ')
    
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
    
    if len(sentences) < 3:
        return []
    
    results = []
    
    for i in range(1, len(sentences) - 1):
        result = {
            'index': i,
            'previous': sentences[i-1],
            'current': sentences[i],
            'next': sentences[i+1],
            'concatenated': separator.join([sentences[i-1], sentences[i], sentences[i+1]])
        }
        results.append(result)
    
    return results


def sentence_by_SaT_with_metadata(input_transcript:dict[str, dict[str]], model:str=config["SaT_model"], threshold:float=config["SaT_threshold"]) -> dict[str, list[dict]]:
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
    result:dict[str, list[dict]] = {}

    for youtube_id, youtube_transcripts_data in input_transcript.items(): # Each video

        Full_text:str = YouTubeTranscript_to_text(youtube_transcripts_data['transcription']) # "hi everyone so I've wanted to make this video for a while it is a comprehensive"
        segmented_text_by_SaT = sentence_by_SaT(text=Full_text, model=model, threshold=threshold) # ["hi everyone so I've wanted to make this video for a while", "it is a comprehensive", ...]
        concatenated_text_by_SaT = concatenate_with_neighbors_detailed(sentences=segmented_text_by_SaT, separator=' ') # ["hi everyone so I've wanted to make this video for a while it is a comprehensive", ...]
        
        raw_index, sents_with_metadata = 0, [] # raw_index: 0, sents_with_metadata: [], initionalization

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
                        "text":sentence,
                        "start":start_at_sentence, 
                        "end":round(end_at_sentence,3), 
                        "title":youtube_transcripts_data['video_info']['title'],
                        "channelTitle":youtube_transcripts_data['video_info']['channelTitle'],
                        "publishedAt":youtube_transcripts_data['video_info']['publishedAt']
                    })
                    break


        result[youtube_id] = sents_with_metadata

    return result

def main():
    raw_transcript:dict[str, dict[str]] = input_file_loader(INPUT_FILE_PATH_WITH_NAME)
    previous_processed_video:dict[str, list[dict]] = output_file_loader(OUTPUT_FILE_PATH_WITH_NAME)

    filtered_transcript:dict[str, dict[str]] = {}

    for youtube_id in raw_transcript.keys():
        if youtube_id not in list(previous_processed_video.keys()):
            filtered_transcript[youtube_id] = raw_transcript[youtube_id]
        else:
            pass

    current_result = sentence_by_SaT_with_metadata(filtered_transcript, model=config["SaT_model"], threshold=config["SaT_threshold"])
    result = previous_processed_video
    result.update(current_result)
    print("previous processed video: ", len(list(previous_processed_video.keys())))
    print("new processed video: ", len(list(filtered_transcript.keys())))
    save_result_to_file(result=result, file_path=OUTPUT_FILE_PATH_WITH_NAME, backup_file_path=BACKUP_FILE_PATH_WITH_NAME)
    return result


if __name__ == "__main__":
    result = main()
    print("Done!")