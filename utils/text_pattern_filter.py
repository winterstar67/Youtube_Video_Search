import re

def remove_filler_words(text:list[dict]) -> list[dict]:
    """
    STT 텍스트에서 Filler words만 제거하는 함수

    Filler words의 정의:
    - 말하는 사람이 생각을 정리하거나 망설일 때 사용하는 단어들
    - 제거해도 문장의 의미가 변하지 않는 단어들

    제거 대상:
    - uh, um, hmm (대소문자 구분 없음)

    Parameters:
    -----------
    text : list[dict]
        정제할 원본 텍스트 (각 dict는 'text' 키를 포함)

    Returns:
    --------
    list[dict]
        Filler words가 제거된 텍스트
    """

    # 원본 텍스트를 보존
    refined_text = text.copy()

    # 각 dict의 'text' 필드에 대해 처리
    for index in range(len(refined_text)):
        text_content = refined_text[index]['text']

        # 1. "uh" 제거
        # \b는 word boundary로 단어의 경계를 의미
        # "uh"가 단독 단어일 때만 제거되므로 "uhaul"의 "uh"는 보호됨
        text_content = re.sub(r'\b[Uu]h\b', '', text_content)

        # 2. "um" 제거
        # "um"이 단독 단어일 때만 제거
        text_content = re.sub(r'\b[Uu]m\b', '', text_content)

        # 3. "hmm" 제거 (hmmm, hmmmm 등 m이 여러 개인 변형도 포함)
        # [Hh]m+는 "h" 또는 "H" 다음에 "m"이 1개 이상 오는 패턴
        text_content = re.sub(r'\b[Hh]m+\b', '', text_content)

        # 4. 여러 개의 연속된 공백을 하나로 정리
        # Filler words 제거 후 생긴 중복 공백 정리
        text_content = re.sub(r'\s+', ' ', text_content)

        # 5. 문장 부호 앞의 불필요한 공백 제거
        # 예: "word , another" -> "word, another"
        text_content = re.sub(r'\s+([,.!?;:])', r'\1', text_content)

        # 6. 처리된 텍스트를 다시 저장
        refined_text[index]['text'] = text_content.strip()

    return refined_text

def remove_short_text(text_list:list[dict], min_length:int=10) -> list[dict]:
    """
    Remove short text

    Parameters:
    -----------
    text_list : list[dict]
        텍스트 리스트 (각 dict는 'text' 키를 포함)
    min_length : int
        최소 텍스트 길이 (기본값: 10)

    Returns:
    --------
    list[dict]
        min_length보다 긴 텍스트만 포함된 리스트
    """
    result:list[dict] = []
    for item in text_list:
        if len(item['text']) > min_length:
            result.append(item)
        else:
            pass
    return result

def main():
    sample_text = "I want to show you how I use these tools and how you can also use them uh in your own life and work"
    print(remove_filler_words(sample_text))

    sample_text = "uh I need to rent from uhaul um for moving hmm"
    print(remove_filler_words(sample_text))

# 사용 예시 및 테스트
if __name__ == "__main__":
    main()