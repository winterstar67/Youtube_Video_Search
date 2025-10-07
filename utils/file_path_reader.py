import os
from datetime import datetime

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
    return BACKUP_FILE_PATH_WITH_NAME

def main():
    backup_file_path_reader(output_file_name="test", output_file_extension="json")

if __name__ == "__main__":
    main()