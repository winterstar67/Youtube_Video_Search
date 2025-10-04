"""
Test script to load Youtube_transcription.pkl file

This script attempts to load the pickle file and display its contents
to verify that the save/load process works correctly.
"""
import pickle
import os
from pprint import pprint

# File path configuration
PICKLE_FILE_PATH = "data/results/Youtube_transcription.pkl"

def test_load_transcription():
    """
    Load and display the Youtube transcription pickle file
    """
    if not os.path.exists(PICKLE_FILE_PATH):
        print(f"❌ File not found: {PICKLE_FILE_PATH}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Absolute path checked: {os.path.abspath(PICKLE_FILE_PATH)}")
        return None

    try:
        with open(PICKLE_FILE_PATH, "rb") as f:
            youtube_transcription_dict = pickle.load(f)

        print(f"✅ Successfully loaded pickle file from: {PICKLE_FILE_PATH}")
        print(f"\nNumber of videos: {len(youtube_transcription_dict)}")
        print(f"\nVideo links:")
        for idx, link in enumerate(youtube_transcription_dict.keys(), 1):
            print(f"  {idx}. {link}")

        print("\n" + "="*80)
        print("Full dictionary structure:")
        print("="*80)
        pprint(youtube_transcription_dict)

        return youtube_transcription_dict

    except Exception as e:
        print(f"❌ Error loading pickle file: {type(e).__name__}: {e}")
        return None

if __name__ == "__main__":
    result = test_load_transcription()

    if result is not None:
        print("\n" + "="*80)
        print("✅ Test PASSED: Pickle file loaded successfully")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ Test FAILED: Could not load pickle file")
        print("="*80)
