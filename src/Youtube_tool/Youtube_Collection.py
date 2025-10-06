import os
import json
import yaml
import requests
import pandas as pd
import numpy as np
from googleapiclient.discovery import build
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
from Youtube_tool.ID_extraction import extract_video_id

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=API_KEY)
video_id_list = []

# === File path configuration ===

current_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.dirname(current_path)
root_path = os.path.dirname(parent_path)

INPUT_FILE_PATH = os.path.join(root_path, "data", "external_data")
INPUT_FILE_NAME = "video_link_target.yaml"
INPUT_FILE_PATH_WITH_NAME = os.path.join(INPUT_FILE_PATH, INPUT_FILE_NAME)

OUTPUT_FILE_PATH = os.path.join(root_path, "data", "results")
OUTPUT_FILE_NAME = "Youtube_video_info"
OUTPUT_FILE_EXTENSION = "json"
OUTPUT_FILE_PATH_WITH_NAME = os.path.join(OUTPUT_FILE_PATH, OUTPUT_FILE_NAME) + "." + OUTPUT_FILE_EXTENSION

BACKUP_FILE_PATH = os.path.join(root_path, "backup")
BACKUP_FILE_NAME = f"{OUTPUT_FILE_NAME}_{datetime.now().strftime('%Y%m%d')}.{OUTPUT_FILE_EXTENSION}"
BACKUP_FILE_PATH_WITH_NAME = os.path.join(BACKUP_FILE_PATH, BACKUP_FILE_NAME)

# === Function definition ===
def input_file_loader(input_file_path:str=INPUT_FILE_PATH_WITH_NAME):
    with open(input_file_path, "r") as f:
        video_url_list = yaml.safe_load(f)
    return video_url_list

def video_id_list_loader(video_url_list:dict):
    for video_url in video_url_list['target_video_link']:
        video_id = extract_video_id(video_url)
        video_id_list.append(video_id)
    return video_id_list

def request_to_youtube(video_url_list:dict):
    video_id_list = video_id_list_loader(video_url_list)
    request = youtube.videos().list(
        part = "snippet",
        regionCode = "US",
        id = video_id_list
    )
    return request

def response_from_youtube(video_url_list:dict):
    request = request_to_youtube(video_url_list)
    response = request.execute()['items']
    return response

def extract_info_from_response(response:list[dict]):
    """
    Input: response from youtube

    Output: extracted result
    - type: dict[str, dict]
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
    """
    extracted_result = {}
    KST = timezone(timedelta(hours=9))
    for item in response:
        extracted_result[item['id']] = {
            'title': item['snippet']['title'],
            'channelTitle': item['snippet']['channelTitle'],
            'description': item['snippet']['description'],
            'publishedAt': item['snippet']['publishedAt'],
            'channelId': item['snippet']['channelId'],
            'defaultLanguage': item['snippet']['defaultLanguage'],
            'categoryId': item['snippet']['categoryId'],
            'created_datetime_UTC9': datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')
        }
    return extracted_result

def save_result_to_file(response:dict):
    with open(OUTPUT_FILE_PATH_WITH_NAME, "w") as f:
        json.dump(response, f)
    
    with open(BACKUP_FILE_PATH_WITH_NAME, "w") as f:
        json.dump(response, f)

def main():
    video_url_list = input_file_loader()
    response = response_from_youtube(video_url_list)
    extracted_result = extract_info_from_response(response)
    save_result_to_file(extracted_result)
    return extracted_result

# === Main function ===
if __name__ == "__main__":
    response = main()
    print(response)