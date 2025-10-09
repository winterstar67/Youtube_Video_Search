import os
from datetime import datetime
import json
import pickle
import pandas as pd
import yaml

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

def backup_file_path_reader(output_file_name:str, output_file_extension:str) -> str:
    """
    Define backup file path
    """
    BACKUP_FILE_PATH:str = os.path.join(parent_dir, "backup" + "/" + datetime.now().strftime('%Y%m%d'))
    if not os.path.exists(BACKUP_FILE_PATH):
        os.makedirs(BACKUP_FILE_PATH, exist_ok=True)
    else:
        pass
    BACKUP_FILE_NAME:str = f"{output_file_name}_{datetime.now().strftime('%Y%m%d')}.{output_file_extension}"
    BACKUP_FILE_PATH_WITH_NAME:str = os.path.join(BACKUP_FILE_PATH, BACKUP_FILE_NAME)
    return BACKUP_FILE_PATH, BACKUP_FILE_PATH_WITH_NAME

def file_loader(file_path:str, file_name:str, file_extension:str) -> dict:
    """
    Load file

    Input: file_path type
        - example: "../data/results/transcript_by_sentence.json"

    Output: file content
    """
    try:
        file_path_with_name = file_path + "/" + file_name + "." + file_extension
        if not os.path.exists(file_path_with_name):
            raise FileNotFoundError(f"File not found: {file_path_with_name}")

        loaders = {
            "json": lambda path: json.load(open(path, "r")),
            "csv": lambda path: pd.read_csv(path),
            "pkl": lambda path: pickle.load(open(path, "rb")),
            "yaml": lambda path: yaml.safe_load(open(path, "r"))
        }
        result = loaders[file_extension](file_path_with_name)
        print(f"File loaded: {file_path_with_name}")
        return result
    except Exception as e:
        print(f"No path found. \n None will be returned.")
        return None

def check_file_path_existence(file_path:str, backup_file_path:str) -> None:
    """
    Check if the file path exists
    """
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File path not found: {file_path}")
        if not os.path.exists(backup_file_path):
            raise FileNotFoundError(f"Backup file path not found: {backup_file_path}")
    except Exception as e:
        print(f"Error at {__file__}'s check_file_path_existence: " + str(e))
        return None

def save_result_to_file(result:dict[str, list[dict]], file_path:str, file_name:str, file_extension:str) -> None:
    """
    Save result to file
    """
    # === file path definition ===
    try:
        full_path = os.path.join(file_path, f"{file_name}.{file_extension}")
        backup_file_path, backup_file_path_with_name = backup_file_path_reader(output_file_name=file_name, output_file_extension=file_extension)

        check_file_path_existence(file_path=file_path, backup_file_path=backup_file_path)

        # === Save function definition ===
        def save_json(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)

        def save_csv(path):
            result.to_csv(path, index=False)

        def save_pkl(path):
            with open(path, "wb") as f:
                pickle.dump(result, f)

        def save_yaml(path):
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(result, f, allow_unicode=True)

        # === Save function selection ===
        savers = {
            "json": save_json,
            "csv": save_csv,
            "pkl": save_pkl,
            "yaml": save_yaml,
        }
        # === Exception handling ===
        if file_extension not in savers:
            raise ValueError(f"Invalid file extension: {file_extension}")

        # === Save file ===
        for path in (full_path, backup_file_path_with_name):
            savers[file_extension](path)
        print(f"Backup and File are saved")
    except Exception as e:
        print(f"Error at {__file__}'s save_result_to_file: " + str(e))

def concat_data(prev_data, current_data, file_extension:str):
    """
    Concatenate previous data and current data based on file extension

    Args:
        prev_data: Previous data (DataFrame for csv, dict for json)
        current_data: Current data (DataFrame for csv, dict for json)
        file_extension: File extension ('csv' or 'json')

    Returns:
        Concatenated data in the same format as input

    Example:
        # For CSV
        >>> prev_df = pd.DataFrame({'id': [1], 'name': ['A']})
        >>> current_df = pd.DataFrame({'id': [2], 'name': ['B']})
        >>> result = concat_data(prev_df, current_df, 'csv')
        # result: DataFrame with rows [1, 'A'] and [2, 'B']

        # For JSON
        >>> prev_dict = {'key1': 'value1'}
        >>> current_dict = {'key2': 'value2'}
        >>> result = concat_data(prev_dict, current_dict, 'json')
        # result: {'key1': 'value1', 'key2': 'value2'}
    """
    try:
        if file_extension == 'csv':
            # CSV: concatenate along axis=0 (rows)
            return pd.concat([prev_data, current_data], axis=0, ignore_index=True)
        elif file_extension == 'json':
            # JSON: merge dictionaries (current_data overwrites prev_data for duplicate keys)
            merged = prev_data.copy()
            merged.update(current_data)
            return merged
        else:
            raise ValueError(f"Unsupported file extension: {file_extension}. Only 'csv' and 'json' are supported.")
    except Exception as e:
        print(f"Error at {__file__}'s concat_data: " + str(e))

def load_video_config(file_path:str=None) -> dict:
    """
    Load video_link_target.yaml file

    Input: file_path (optional)
        - If not provided, defaults to data/external_data/video_link_target.yaml

    Output: dict
        - Full YAML content including video URLs and config settings
        - Keys: video URLs (e.g., "https://www.youtube.com/watch?v=...")
        - Values: config dict containing index_name, namespace, cloud, region, embed, Author, Comment, etc.

    Example:
        {
            "https://www.youtube.com/watch?v=EWvNQjAaOHw": {
                "index_name": "developer-quickstart-py",
                "namespace": "test",
                "cloud": "aws",
                "region": "us-east-1",
                "embed": {
                    "model": "llama-text-embed-v2",
                    "field_map": {"text": "chunk_text"}
                },
                "Author": "Andrew Ng",
                "Comment": "Machine Learning course"
            },
            ...
        }
    """
    try:
        if file_path is None:
            file_path = os.path.join(parent_dir, "data", "external_data", "video_link_target.yaml")

        with open(file_path, "r", encoding="utf-8") as f:
            video_url_list = yaml.safe_load(f)

        return video_url_list
    
    except Exception as e:
        print(f"Error at {__file__}'s load_video_config: " + str(e))
        return {}

def main():
    pass

if __name__ == "__main__":
    main()