"""
GPT-based Weird Word Sensor

Order in pipeline: Optional (between Youtube_transcription.py and transcript_processing.py)

Function:
    1. Load Youtube_transcription.pkl
    2. Extract first 6000 characters of full text from each video
    3. Use GPT-4o-mini to detect typos and weird words in auto-generated subtitles (Multi-threaded)
    4. Return corrections in dictionary format: {"typo/weird_word": "corrected_word"}
    5. Save results for each video

Input:
    - File: data/results/Youtube_transcription.pkl
    - File: data/results/Youtube_video_info.json (for video title context)

Output:
    - File: data/results/typo_corrections.json
    - Format: {
        "video_id1": {"typo1": "correction1", "typo2": "correction2", ...},
        "video_id2": {...},
        ...
      }

Usage:
    This helps identify and correct common auto-generated subtitle errors before
    processing the transcripts into sentence chunks.

Performance:
    Uses ThreadPoolExecutor for parallel processing of multiple videos.
"""

import os
import sys
import json
import pickle
from datetime import datetime
from openai import OpenAI
import dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

dotenv.load_dotenv()

# Path configuration
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from utils.file_path_reader import file_loader, save_result_to_file

# Input files
TRANSCRIPTION_FILE_PATH = os.path.join(parent_dir, "data", "results")
TRANSCRIPTION_FILE_NAME = "Youtube_transcription"
TRANSCRIPTION_FILE_EXTENSION = "pkl"

VIDEO_INFO_FILE_PATH = os.path.join(parent_dir, "data", "results")
VIDEO_INFO_FILE_NAME = "Youtube_video_info"
VIDEO_INFO_FILE_EXTENSION = "json"

# Output file
OUTPUT_FILE_PATH = os.path.join(parent_dir, "data", "results", "gpt_based_weired_word_sensor")
OUTPUT_FILE_NAME = "typo_corrections"
OUTPUT_FILE_EXTENSION = "json"

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Model configuration
GPT_MODEL = "gpt-4o-mini"  # Using gpt-4o-mini (latest available model)
MAX_TEXT_LENGTH = 6000
MAX_WORKERS = 5  # Number of parallel threads

# Thread-safe print lock
print_lock = Lock()


def thread_safe_print(*args, **kwargs):
    """Thread-safe print function"""
    with print_lock:
        print(*args, **kwargs)


def YouTubeTranscript_to_text(youtube_transcript) -> str:
    """
    Convert YouTubeTranscript to full text

    Input: YouTubeTranscript (list of FetchedTranscriptSnippet objects)
    Output: Full text string
    """
    text = ""
    for snippet in youtube_transcript:
        text += " " + snippet.text
    return text.strip()


def create_typo_detection_prompt(full_text: str, video_title: str) -> str:
    """
    Create prompt for GPT to detect typos and weird words

    Parameters:
    - full_text: First 6000 characters of transcript
    - video_title: Video title for context

    Returns:
    - Formatted prompt string
    """
    prompt = f"""You are an expert proofreader analyzing auto-generated YouTube subtitles.

Video Title: "{video_title}"

Task: Analyze the following auto-generated subtitle text and identify ONLY typos or nonsensical words that need correction. Use STRICT criteria - only flag clear errors.

Auto-generated Subtitle Text:
\"\"\"{full_text}\"\"\"

Instructions:
1. Identify typos (misspelled words)
2. Identify nonsensical/non-existent words that don't fit the context
3. For each error, provide the corrected version based on context
4. Be STRICT - only include obvious errors, not stylistic choices or valid informal language
5. Consider the video title for context

Output ONLY a valid JSON object in this exact format (no additional text):
{{
  "typo_or_weird_word_1": "corrected_word_1",
  "typo_or_weird_word_2": "corrected_word_2"
}}

If no errors are found, return: {{}}

Important:
- Return ONLY the JSON object, no explanations or additional text
- Use double quotes for JSON keys and values
- If a word appears multiple times with the same error, only list it once
"""
    return prompt


def detect_typos_with_gpt(full_text: str, video_title: str, video_id: str) -> dict:
    """
    Use GPT to detect typos and weird words in auto-generated subtitles

    Parameters:
    - full_text: Full transcript text
    - video_title: Video title for context
    - video_id: Video ID for logging

    Returns:
    - Dictionary of typo corrections: {"typo": "correction", ...}
    """
    try:
        # Truncate text to first 6000 characters
        text_sample = full_text[:MAX_TEXT_LENGTH]

        thread_safe_print(f"[{video_id}] Analyzing...")
        thread_safe_print(f"[{video_id}]   Title: {video_title}")
        thread_safe_print(f"[{video_id}]   Text length: {len(text_sample)} characters")

        # Create prompt
        prompt = create_typo_detection_prompt(text_sample, video_title)

        # Call GPT API
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert proofreader. You return ONLY valid JSON objects with no additional text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3,  # Lower temperature for more consistent output
            max_tokens=1000,
            response_format={"type": "json_object"}  # Ensure JSON response
        )

        # Parse response
        result_text = response.choices[0].message.content.strip()
        corrections = json.loads(result_text)

        thread_safe_print(f"[{video_id}]   Found {len(corrections)} corrections")
        if corrections:
            thread_safe_print(f"[{video_id}]   Sample: {list(corrections.items())[:3]}")
        thread_safe_print(f"[{video_id}] ✓ Complete")

        return corrections

    except json.JSONDecodeError as e:
        thread_safe_print(f"[{video_id}]   ✗ Error parsing JSON: {e}")
        return {}

    except Exception as e:
        thread_safe_print(f"[{video_id}]   ✗ Error: {str(e)}")
        return {}


def process_single_video(video_id: str, video_data: dict, video_info: dict) -> tuple:
    """
    Process a single video (designed for parallel execution)

    Parameters:
    - video_id: YouTube video ID
    - video_data: Video transcription data
    - video_info: Video metadata dictionary

    Returns:
    - Tuple of (video_id, corrections_dict)
    """
    # Get video title
    if video_id in video_info:
        video_title = video_info[video_id].get("title", "Unknown Title")
    else:
        video_title = video_data.get("video_info", {}).get("title", "Unknown Title")

    # Convert transcript to full text
    full_text = YouTubeTranscript_to_text(video_data["transcription"])

    # Detect typos using GPT
    corrections = detect_typos_with_gpt(full_text, video_title, video_id)

    return (video_id, corrections)


def load_video_info(file_path: str, file_name: str, file_extension: str) -> dict:
    """
    Load video info JSON file

    Returns:
    - Dictionary: {video_id: {title, channelTitle, ...}, ...}
    """
    file_path_with_name = os.path.join(file_path, f"{file_name}.{file_extension}")

    try:
        with open(file_path_with_name, "r", encoding="utf-8") as f:
            video_info = json.load(f)
        print(f"Loaded video info for {len(video_info)} videos")
        return video_info
    except FileNotFoundError:
        print(f"Warning: Video info file not found at {file_path_with_name}")
        return {}
    except Exception as e:
        print(f"Error loading video info: {e}")
        return {}


def load_transcriptions(file_path: str, file_name: str, file_extension: str) -> dict:
    """
    Load transcription pickle file

    Returns:
    - Dictionary: {video_id: {transcription: [...], video_info: {...}}, ...}
    """
    file_path_with_name = os.path.join(file_path, f"{file_name}.{file_extension}")

    try:
        with open(file_path_with_name, "rb") as f:
            transcriptions = pickle.load(f)
        print(f"Loaded transcriptions for {len(transcriptions)} videos")
        return transcriptions
    except FileNotFoundError:
        print(f"Error: Transcription file not found at {file_path_with_name}")
        return {}
    except Exception as e:
        print(f"Error loading transcriptions: {e}")
        return {}


def main():
    """
    Main function to detect typos in all video transcriptions (Multi-threaded)
    """
    print("GPT-based Typo Detection (Multi-threaded)")
    print()

    all_corrections = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks
        future_to_video = {
            executor.submit(process_single_video, video_id, video_data, video_info): video_id
            for video_id, video_data in transcriptions.items()
        }

        # Collect results as they complete
        completed = 0
        total = len(future_to_video)

        for future in as_completed(future_to_video):
            video_id = future_to_video[future]
            try:
                vid, corrections = future.result()
                all_corrections[vid] = corrections
                completed += 1
                thread_safe_print(f"\nProgress: {completed}/{total} videos processed\n")
            except Exception as e:
                thread_safe_print(f"[{video_id}] ✗ Exception: {str(e)}")
                all_corrections[video_id] = {}
                completed += 1

    # Save results
    save_result_to_file(
        result=all_corrections,
        file_path=OUTPUT_FILE_PATH,
        file_name=OUTPUT_FILE_NAME,
        file_extension=OUTPUT_FILE_EXTENSION
    )

    # Summary
    total_videos = len(all_corrections)
    videos_with_corrections = sum(1 for c in all_corrections.values() if c)
    total_corrections = sum(len(c) for c in all_corrections.values())

    print()
    print("Summary:")
    print(f"  Total videos analyzed: {total_videos}")
    print(f"  Videos with corrections: {videos_with_corrections}")
    print(f"  Total corrections found: {total_corrections}")
    print(f"  Results saved to: {OUTPUT_FILE_NAME}.{OUTPUT_FILE_EXTENSION}")
    print(f"  Parallel workers used: {MAX_WORKERS}")
    print("=" * 70)

    return all_corrections


if __name__ == "__main__":
    try:
        results = main()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
