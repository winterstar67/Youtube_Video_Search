from urllib.parse import urlparse, parse_qs

def extract_video_id(url: str) -> str | None:
    """
    YouTube URL에서 videoId를 추출.
    지원 예시:
     - https://www.youtube.com/watch?v=VIDEO_ID
     - https://youtu.be/VIDEO_ID
     - https://www.youtube.com/embed/VIDEO_ID
     - https://www.youtube.com/v/VIDEO_ID
    """
    parsed = urlparse(url)
    host = parsed.netloc
    path = parsed.path

    # 예: youtu.be/VIDEO_ID
    if host in ("youtu.be", "www.youtu.be"):
        # path 시작 "/" 이후 부분이 ID
        return path.lstrip("/")

    # 예: www.youtube.com/watch?v=VIDEO_ID
    if host in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        # 쿼리 파라미터 중 v 값을 봄
        qs = parse_qs(parsed.query)
        if "v" in qs:
            return qs["v"][0]

        # embed 형식 등
        # /embed/VIDEO_ID
        if path.startswith("/embed/"):
            return path.split("/")[2]
        # /v/VIDEO_ID
        if path.startswith("/v/"):
            return path.split("/")[2]

    return None  # ID를 못 찾았을 경우