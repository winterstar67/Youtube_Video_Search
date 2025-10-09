from yt_dlp import YoutubeDL
import time
import random

def download_youtube_video(url_path:str, output_path:str, output_folder_name:str):
    with open(url_path, "r") as f:
        urls = f.readlines()
    folder_name = output_folder_name

    # 137: 1080p video, 140: m4a audio
    ydl_opts = {
        'sleep_interval': 60,         # 각 영상 사이 최소 5초 대기
        'max_sleep_interval': 120,    # 각 영상 사이 최대 10초 대기 (랜덤)
        'socket_timeout': 120,  # 초 단위, 예: 60초
        'retries': 3,  # 최대 10회 재시도
        'overwrites': False,
        'writeinfojson': True,  # 메타데이터 저장
        'write_thumbnail': True,  # 썸네일 저장
        'subtitleslangs': ['en'],  # 영어 자막 다운로드
        'format': '399+bestaudio/398+bestaudio/bestvideo+bestaudio',  # 1080p 비디오 + m4a 오디오 병합
        'outtmpl': f'{output_path}/{folder_name}/%(title)s.%(ext)s'  # 저장 파일명 템플릿
    }
    for index in range(len(urls)):
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([urls[index]])

        if index < (len(urls) - 1):
            random_number = random.uniform(50, 70)
            time.sleep(random_number)