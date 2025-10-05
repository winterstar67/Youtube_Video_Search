"""
Store on VectorDB

Order in pipeline: Third (3)

Function:
    1. transcript_processing.py에서 받은 데이터를 VectorDB에 저장

Input:    

Output:
    - VectorDB에 저장된 데이터
"""

import os
import json
from pinecone import Pinecone, ServerlessSpec

import os
import dotenv

dotenv.load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_HOST = os.getenv("PINECONE_HOST")

# === File path Configuration ===

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

INPUT_FILE_PATH = os.path.join(parent_dir, "data", "results")
INPUT_FILE_NAME = "transcript_by_sentence.json"
INPUT_FILE_PATH_WITH_NAME = os.path.join(INPUT_FILE_PATH, INPUT_FILE_NAME)

# OUTPUT_FILE_PATH = os.path.join(parent_dir, "data", "results")
# OUTPUT_FILE_NAME = "VectorDB_data.pkl"
# OUTPUT_FILE_PATH_WITH_NAME = os.path.join(OUTPUT_FILE_PATH, OUTPUT_FILE_NAME)

# BACKUP_FILE_PATH = os.path.join(parent_dir, "backup")
# BACKUP_FILE_NAME = "VectorDB_data.pkl"
# BACKUP_FILE_PATH_WITH_NAME = os.path.join(BACKUP_FILE_PATH, BACKUP_FILE_NAME)

### === VectorDB Configuration ===
config = {
    "index_name": "developer-quickstart-py",
    "namespace": "test",
    "cloud": "aws",
    "region": "us-east-1",
    "embed": {
        "model":"llama-text-embed-v2",
        "field_map":{"text": "chunk_text"}
    }
}

# === Load data ===
def intput_data_loader(input_file_path:str=INPUT_FILE_PATH_WITH_NAME) -> dict:
    """
    Load input data from json file
    Input: input_file_path type
        - example: "data/results/transcript_by_sentence.json"

    Output: dict[str, list[dict]] type
        - example:
          {
            "https://www.youtube.com/watch?v=EWvNQjAaOHw": [
                {text: 'hi everyone so in this video I would', start: 0.12, duration: 3.72}, 
                {text: 'like to continue our general audience', start: 2.159, duration: 5.041}, 
                {text: 'series on large language models like', start: 3.84, duration: 5.839},
                ...
            ]
          }
    """
    with open(input_file_path, "r") as f:
        result = json.load(f)
    return result

# === Connect to VectorDB ===
# Check (Completed)
def connect_to_Pinecone(api_key:str=PINECONE_API_KEY) -> Pinecone: # Level 1 (Pinecone Level)
    """
    Input: api_key type
        - example: PINECONE_API_KEY

    Output: Pinecone type
        - example: Pinecone(api_key=PINECONE_API_KEY)
    """
    return Pinecone(api_key=api_key)

# Check (Completed)
def connect_to_Index(pc:Pinecone, host:str=PINECONE_HOST) -> "Pinecone.Index": # Level 2 (Index Level)
    """
    Connect to Index
    Input: pc, host
        - pc: Pinecone(api_key=PINECONE_API_KEY)
        - host: str type
            - example: PINECONE_HOST

    Output: Pinecone.Index type
        - example: Pinecone.Index(host=PINECONE_HOST)
    """
    return pc.Index(host=host)

# Check (Completed)
def check_index_list(pc:Pinecone) -> list[str]: # Level 2 (Index Level)
    """
    Check index list
    Input: pc type
        - example: Pinecone(api_key=PINECONE_API_KEY)

    Output: list[str] type
        - example: ["index_name1", "index_name2", ...]
    """
    result = pc.list_indexes().names()
    return result

# Check (Completed)
def check_index_existence(index_list:list[str], index_name:str) -> bool: # Level 2 (Index Level)
    """
    Check index existence
    Input: index_list, index_name
        - index_list: list[str] type
            - example: ["index_name1", "index_name2", ...]
        - index_name: str type
            - example: "index_name"

    Output: bool type
        - example: True
    """
    return index_name in index_list

def check_namespace_list(pc_index:"Pinecone.Index") -> dict[str, int]: # Level 3 (namespace Level)
    """
    Check namespace
    Input: pc_index
        - pc_index: Pinecone.Index(host=PINECONE_HOST)

    Output: dict[str, int] type
        - example: {"namespace1": "id_count", "namespace2": "id_count", ...}

    pc_index.list_namespaces()를 대체 가능한 함수: 
        - pc_index.describe_namespace(namespace=namespace)
            - {"name": "test", "record_count": "2"}

        - pc_index.namespace.list_paginated()
            - {"namespaces": [{
                    "name": "test",
                    "record_count": "2"}]}
        - pc_index.describe_index_stats()
            - { 'dimension': 1024,
                'index_fullness': 0.0,
                'metric': 'cosine',
                'namespaces': {'test': {'vector_count': 2}},
                'total_vector_count': 2,
                'vector_type': 'dense'}
    """
    namespace_list = list(pc_index.list_namespaces()) # pc_index.list_namespaces() 결과가 generator 여서 list를 적용해줘야 함.
    result = {item["name"]: int(item["record_count"]) for item in namespace_list} # namespace_list를 dictionary 형태로 변환

    return result

def get_namespace_len(pc_index:"Pinecone.Index", namespace:str) -> int: # Level 3 (namespace Level)
    """
    Get namespace length
    Input: pc_index, namespace
        - pc_index: Pinecone.Index(host=PINECONE_HOST)
        - namespace: "namespace"
    
    Output: int type
        - example: 2
    """
    return pc_index.describe_index_stats()["namespaces"][namespace]["vector_count"]

def namespace_checker(namespace_list:list[str], namespace:str) -> bool: # Level 3 (namespace Level)
    """
    Check namespace
    Input: namespace_list, namespace
        - namespace_list: ["namespace1", "namespace2", ...]
        - namespace: "namespace"

    Output: Bool type
        - example: True
    """
    return namespace in namespace_list

def records_id_sampling(pc_index:"Pinecone.Index", limit:int=3, namespace:str="default") -> list[str]: # Level 3 (namespace Level)
    """
    Sampling records id
    Input: pc_index, limit, namespace
        - pc_index: Pinecone.Index(host=PINECONE_HOST)
        - limit: int type
        - namespace: "namespace"
    """
    result = pc_index.list_paginated(
            prefix="",
            limit=limit,
            namespace=namespace
        )
    print("records_id_sampling result: ", result)
    return result

def create_index(pc:Pinecone, index_name:str) -> None: # Level 2 (Index Level)
    """
    Create index with user defined embedding model (No integrated model)
    Input: pc, index_name
        - pc: Pinecone(api_key=PINECONE_API_KEY)
        - index_name: "index_name"
    
    Output: None
        - Just create index with user defined embedding model (No integrated model)
    """
    pc.create_index(index_name, metric="cosine", spec=ServerlessSpec())

def create_integrated_model_index(pc:Pinecone, index_name:str, config:dict) -> None:
    """
    Create index with integrated model
    Input: pc, index_name, config
        - pc: Pinecone(api_key=PINECONE_API_KEY)
        - index_name: "index_name"
        - config: dict type
            - example: {"cloud": "aws", "region": "us-east-1", "embed": {"model": "llama-text-embed-v2", "field_map": {"text": "chunk_text"}}}
    
    Output: None
        - Just create index with integrated model
    """
    if not pc.has_index(index_name):
        pc.create_index_for_model(
            name=index_name,
            cloud=config["cloud"],
            region=config["region"],
            embed={
                "model":config["embed"]["model"],
                "field_map":config["embed"]["field_map"]
            }
        )
    else:
        print("The index already exist")

def upsert_data(pc_index:"Pinecone.Index", vectors:list[dict], namespace:str="default") -> None: # Level 2 (Index Level)
    """
    It's for user defined embedding model
    Input: pc_index, vectors, namespace
        - pc_index: Pinecone.Index(host=PINECONE_HOST)
        - vectors: [
                        {
                        "id": "vec1", 
                        "values": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1], 
                        "metadata": {"genre": "comedy", "year": 2020}
                        },
                        {
                        "id": "vec2", 
                        "values": [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2],
                        "metadata": {"genre": "documentary", "year": 2019}
                        }
                    ],
        - namespace: "namespace"
    
    Output: None
        - Just upsert vectors data
    """
    pc_index.upsert(vectors, namespace=namespace)

def upsert_records(pc_index:"Pinecone.Index", records:list[dict], namespace:str="default") -> None: # Level 2 (Index Level)
    """
    It's for integrated model
    Input: pc_index, vectors, namespace
        - pc_index: Pinecone.Index(host=PINECONE_HOST)
        - records: [
                    {
                        "_id": "rec1",
                        "chunk_text": "Apples are a great source of dietary fiber, which supports digestion and helps maintain a healthy gut.",
                        "category": "digestive system", 
                    },
                    {
                        "_id": "rec2",
                        "chunk_text": "Apples originated in Central Asia and have been cultivated for thousands of years, with over 7,500 varieties available today.",
                        "category": "cultivation",
                    },
                    ...
                ]
        - namespace: "namespace"

    Output: None
        - Just upsert records data
    """
    pc_index.upsert_records(records, namespace=namespace)

### === Data Processing ===

def transcript_to_record(id:str, transcript_data:dict) -> dict:
    """
    Convert transcript data to record
    Input: transcript_data
        - transcript_data: dict type
            - example: {"text": "Hello, world!", "start": 0.12, "end": 3.72},

    Output: list[dict] type
        - example: {"id": "rec1", "text": "Hello, world!", metadata: str({"start": 0.12, "end": 3.72})}
    """
    return {"id": id, f"{config["embed"]["field_map"]['text']}": transcript_data["text"], "metadata": str({"start": transcript_data["start"], "duration": transcript_data["end"]})}

def transcript_to_record_batch(transcript_data:list[dict], pc_index:"Pinecone.Index", namespace:str) -> list[dict]:
    """
    Convert transcript data to record
    Input: transcript_data
        - transcript_data: list[dict] type
            - example: [
                        {"text": "Hello, world!", "start": 0.12, "end": 3.72},
                        {"text": "How are you?", "start": 3.73, "end": 5.61},
                        ...
                        ]

    Output: list[dict] type
        - example: [
                {"id": "rec1", "text": "Hello, world!", metadata: str({"start": 0.12, "end": 3.72})}
                {"id": "rec2", "text": "How are you?", metadata: str({"start": 3.73, "end": 5.61})}
                ...
            ]
    """
    result = []
    id_start = get_namespace_len(pc_index=pc_index, namespace=namespace)+1

    for id, record in enumerate(transcript_data, id_start):
        result.append(transcript_to_record(id=id, transcript_data=record))
    return result
    
# def delete_index(pc:Pinecone, index_name:str) -> None:
#     pc.delete_index(index_name)
    



