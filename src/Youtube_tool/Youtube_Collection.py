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
import sys

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=API_KEY)
video_id_list = []

# === File path configuration ===

current_path = os.path.dirname(os.path.abspath(__file__))
parent_path = os.path.dirname(current_path)
root_path = os.path.dirname(parent_path)

sys.path.append(root_path)
from utils.file_path_reader import save_result_to_file, file_loader, concat_data

INPUT_FILE_PATH = os.path.join(root_path, "data", "external_data")
INPUT_FILE_NAME = "video_link_target.yaml"
INPUT_FILE_PATH_WITH_NAME = os.path.join(INPUT_FILE_PATH, INPUT_FILE_NAME)

SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]  # "Youtube_Collection"
OUTPUT_FILE_PATH = os.path.join(root_path, "data", "results", SCRIPT_NAME)
OUTPUT_FILE_NAME = "Youtube_video_info"
OUTPUT_FILE_EXTENSION = "json"

# === Function definition ===
def input_file_loader(input_file_path:str=INPUT_FILE_PATH_WITH_NAME):
    with open(input_file_path, "r") as f:
        video_url_list = yaml.safe_load(f)
    return video_url_list

def video_id_list_loader(video_url_list:dict):
    for video_url in list(video_url_list.keys()):
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

def save_result(current_data:dict, stacked_data:dict):
    """
    Save result using utility function
    This will save to both data/results and backup/{date}/ folders

    Args:
        current_data: Current batch data only (new videos)
        stacked_data: All accumulated data (previous + current)
    """
    # Save current batch only
    save_result_to_file(
        result=current_data,
        file_path=OUTPUT_FILE_PATH,
        file_name=OUTPUT_FILE_NAME,
        file_extension=OUTPUT_FILE_EXTENSION
    )

    # Save stacked version
    save_result_to_file(
        result=stacked_data,
        file_path=OUTPUT_FILE_PATH,
        file_name=OUTPUT_FILE_NAME + "_stacked_version",
        file_extension=OUTPUT_FILE_EXTENSION
    )

def main():
    """
    Main function to collect YouTube video information
    - Loads previous data from Youtube_video_info_stacked_version.json
    - Collects new video information
    - Merges with previous data (stacking)
    - Saves both current batch and stacked version
    """
    # Load previous data
    try:
        prev_youtube_video_infos = file_loader(
            file_path=OUTPUT_FILE_PATH,
            file_name=OUTPUT_FILE_NAME + "_stacked_version",
            file_extension=OUTPUT_FILE_EXTENSION
        )
        if prev_youtube_video_infos is None:
            prev_youtube_video_infos = {}
    except Exception as e:
        print(f"No previous data found. Starting fresh: {e}")
        prev_youtube_video_infos = {}

    # Get current batch of video information
    video_url_list = input_file_loader()
    response = response_from_youtube(video_url_list)
    current_youtube_video_infos = extract_info_from_response(response)

    # Merge previous and current data (stacking)
    stacked_youtube_video_infos = concat_data(
        prev_data=prev_youtube_video_infos,
        current_data=current_youtube_video_infos,
        file_extension='json'
    )

    print(f"Previous videos: {len(prev_youtube_video_infos)}")
    print(f"Current batch: {len(current_youtube_video_infos)}")
    print(f"Total stacked: {len(stacked_youtube_video_infos)}")

    # Save both current and stacked versions
    save_result(
        current_data=current_youtube_video_infos,
        stacked_data=stacked_youtube_video_infos
    )

    return current_youtube_video_infos

# === Main function ===
if __name__ == "__main__":
    response = main()
    print(response)