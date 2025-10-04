import os
import json
import requests
import pandas as pd
import numpy as np
from googleapiclient.discovery import build
from dotenv import load_dotenv
load_dotenv()
from Youtube_tool.ID_extraction import extract_video_id

API_KEY = os.getenv("YOUTUBE_API_KEY")
youtube = build("youtube", "v3", developerKey=API_KEY)
video_id_list = []

with open("data/external_data/video_url_list.txt", "r") as f:
    video_url_list = f.readlines()

for video_url in video_url_list:
    video_id = extract_video_id(video_url)
    video_id_list.append(video_id)

request = youtube.videos().list(
    part = "snippet",
    regionCode = "US",
    id = video_id_list
)
response = request.execute()

with open("data/result/video_transcript_list.json", "w") as f:
    json.dump(response, f)












