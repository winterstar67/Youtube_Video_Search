import re

def remove_filler_words(text):
    """
    STT 텍스트에서 Filler words만 제거하는 함수
    
    Filler words의 정의:
    - 말하는 사람이 생각을 정리하거나 망설일 때 사용하는 단어들
    - 제거해도 문장의 의미가 변하지 않는 단어들
    
    제거 대상:
    - uh, um, hmm (대소문자 구분 없음)
    
    Parameters:
    -----------
    text : str
        정제할 원본 텍스트
    
    Returns:
    --------
    str
        Filler words가 제거된 텍스트
    """
    
    # 원본 텍스트를 보존
    refined_text = text
    
    # 1. "uh" 제거
    # \b는 word boundary로 단어의 경계를 의미
    # "uh"가 단독 단어일 때만 제거되므로 "uhaul"의 "uh"는 보호됨
    refined_text = re.sub(r'\b[Uu]h\b', '', refined_text)
    
    # 2. "um" 제거
    # "um"이 단독 단어일 때만 제거
    refined_text = re.sub(r'\b[Uu]m\b', '', refined_text)
    
    # 3. "hmm" 제거 (hmmm, hmmmm 등 m이 여러 개인 변형도 포함)
    # [Hh]m+는 "h" 또는 "H" 다음에 "m"이 1개 이상 오는 패턴
    refined_text = re.sub(r'\b[Hh]m+\b', '', refined_text)
    
    # 4. 여러 개의 연속된 공백을 하나로 정리
    # Filler words 제거 후 생긴 중복 공백 정리
    refined_text = re.sub(r'\s+', ' ', refined_text)
    
    # 5. 문장 부호 앞의 불필요한 공백 제거
    # 예: "word , another" -> "word, another"
    refined_text = re.sub(r'\s+([,.!?;:])', r'\1', refined_text)
    
    # 6. 문장 시작 부분의 공백 제거
    refined_text = refined_text.strip()
    
    return refined_text

def main():
    sample_text = "I want to show you how I use these tools and how you can also use them uh in your own life and work"
    print(remove_filler_words(sample_text))

    sample_text = "uh I need to rent from uhaul um for moving hmm"
    print(remove_filler_words(sample_text))

# 사용 예시 및 테스트
if __name__ == "__main__":
    main()