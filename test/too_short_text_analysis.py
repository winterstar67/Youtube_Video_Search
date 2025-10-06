import json
from pathlib import Path

def analyze_short_texts(json_file_path, max_length=10):
    """
    JSON 파일에서 'text' 키의 값이 max_length 이하인 모든 텍스트를 중복 제거하여 출력

    Args:
        json_file_path: JSON 파일 경로
        max_length: 최대 텍스트 길이 (기본값: 10)
    """
    # JSON 파일 로드
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 짧은 텍스트 수집 (중복 제거를 위해 set 사용)
    short_texts = set()

    # 데이터가 리스트인 경우
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and 'text' in item:
                text = item['text']
                if len(text) <= max_length:
                    short_texts.add(text)

    # 데이터가 딕셔너리인 경우 (각 키가 비디오 ID 등일 수 있음)
    elif isinstance(data, dict):
        for key, value in data.items():
            # 값이 리스트인 경우
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and 'text' in item:
                        text = item['text']
                        if len(text) <= max_length:
                            short_texts.add(text)
            # 값이 딕셔너리이고 'text' 키를 가진 경우
            elif isinstance(value, dict) and 'text' in value:
                text = value['text']
                if len(text) <= max_length:
                    short_texts.add(text)

    # 결과 출력
    print(f"총 {len(short_texts)}개의 중복 제거된 짧은 텍스트 발견 (길이 <= {max_length}):\n")
    print("=" * 50)

    for idx, text in enumerate(sorted(short_texts), 1):
        print(f"{idx}. '{text}' (길이: {len(text)})")

    return short_texts


if __name__ == "__main__":
    # JSON 파일 경로 설정
    json_path = Path(__file__).parent.parent / "data" / "results" / "transcript_by_sentence.json"

    # 분석 실행
    analyze_short_texts(json_path, max_length=10)
