"""
Test script to read and inspect all data files in the project
"""
import os
import sys
import pickle
import json
import pandas as pd
import yaml

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

def print_section(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80 + "\n")

def inspect_yaml_file(file_path, file_name):
    """Inspect YAML file"""
    print_section(f"Inspecting: {file_name}")
    full_path = os.path.join(file_path, file_name)

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)

        print(f"File: {file_name}")
        print(f"Type: {type(data)}")
        print(f"Keys count: {len(data) if isinstance(data, dict) else 'N/A'}")

        if isinstance(data, dict):
            print(f"\nFirst key: {list(data.keys())[0] if data else 'Empty'}")
            if data:
                first_key = list(data.keys())[0]
                print(f"First value structure:")
                print(f"  Type: {type(data[first_key])}")
                if isinstance(data[first_key], dict):
                    print(f"  Keys: {list(data[first_key].keys())}")
                    print(f"\nSample data:")
                    for k, v in list(data[first_key].items())[:5]:
                        print(f"    {k}: {v}")
    except Exception as e:
        print(f"Error reading {file_name}: {e}")

def inspect_json_file(file_path, file_name):
    """Inspect JSON file"""
    print_section(f"Inspecting: {file_name}")
    full_path = os.path.join(file_path, file_name)

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"File: {file_name}")
        print(f"Type: {type(data)}")

        if isinstance(data, dict):
            print(f"Keys: {list(data.keys())}")
            print(f"\nSample data:")
            for k, v in list(data.items())[:3]:
                print(f"  {k}: {v}")
        elif isinstance(data, list):
            print(f"Length: {len(data)}")
            print(f"First item: {data[0] if data else 'Empty'}")
    except Exception as e:
        print(f"Error reading {file_name}: {e}")

def inspect_csv_file(file_path, file_name):
    """Inspect CSV file"""
    print_section(f"Inspecting: {file_name}")
    full_path = os.path.join(file_path, file_name)

    try:
        df = pd.read_csv(full_path)

        print(f"File: {file_name}")
        print(f"Shape: {df.shape}")
        print(f"Columns: {list(df.columns)}")
        print(f"\nFirst row:")
        print(df.iloc[0].to_dict())
        print(f"\nData types:")
        print(df.dtypes)
    except Exception as e:
        print(f"Error reading {file_name}: {e}")

def inspect_pkl_file(file_path, file_name):
    """Inspect PKL file"""
    print_section(f"Inspecting: {file_name}")
    full_path = os.path.join(file_path, file_name)

    try:
        with open(full_path, 'rb') as f:
            data = pickle.load(f)

        print(f"File: {file_name}")
        print(f"Type: {type(data)}")

        if isinstance(data, dict):
            print(f"Keys count: {len(data)}")
            if data:
                first_key = list(data.keys())[0]
                print(f"\nFirst key: {first_key}")
                print(f"First value type: {type(data[first_key])}")

                if isinstance(data[first_key], dict):
                    print(f"First value keys: {list(data[first_key].keys())}")

                    # Check transcription structure
                    if 'transcription' in data[first_key]:
                        trans = data[first_key]['transcription']
                        print(f"\nTranscription object:")
                        print(f"  Type: {type(trans)}")
                        print(f"  Attributes: {dir(trans)[:10]}...")  # First 10 attributes

                        if hasattr(trans, 'snippets'):
                            snippets = trans.snippets
                            print(f"  Snippets count: {len(snippets)}")
                            if snippets:
                                print(f"  First snippet type: {type(snippets[0])}")
                                print(f"  First snippet: {snippets[0]}")

                    # Check video_info structure
                    if 'video_info' in data[first_key]:
                        info = data[first_key]['video_info']
                        print(f"\nVideo info:")
                        print(f"  Type: {type(info)}")
                        if isinstance(info, dict):
                            print(f"  Keys: {list(info.keys())}")
                            print(f"  Sample values:")
                            for k, v in list(info.items())[:3]:
                                print(f"    {k}: {str(v)[:100]}...")
    except Exception as e:
        print(f"Error reading {file_name}: {e}")

def main():
    print_section("Data File Inspection Report")

    # External data
    external_data_path = os.path.join(parent_dir, "data", "external_data")

    inspect_yaml_file(external_data_path, "video_link_target.yaml")
    inspect_json_file(external_data_path, "query.json")

    # Results data
    results_path = os.path.join(parent_dir, "data", "results")

    inspect_csv_file(results_path, "ID_Table.csv")
    inspect_json_file(results_path, "Youtube_video_info.json")
    inspect_pkl_file(results_path, "Youtube_transcription.pkl")
    inspect_pkl_file(results_path, "Youtube_transcription_stacked_version.pkl")

    print_section("Inspection Complete")

if __name__ == "__main__":
    main()
