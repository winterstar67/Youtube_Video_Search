from youtube_transcript_api import YouTubeTranscriptApi
from Youtube_tool.ID_extraction import extract_video_id

video_id = extract_video_id("https://www.youtube.com/watch?v=EWvNQjAaOHw&t=6026s")

ytt_api = YouTubeTranscriptApi()
print(ytt_api.fetch(video_id))





