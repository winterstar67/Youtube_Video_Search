"""
Store on VectorDB

Order in pipeline: Fourth (4)

Function:
    1. transcript_processing.py에서 받은 데이터를 VectorDB에 저장되는 형태로 변환
    2. Vector DB에 저장

Input:
    1. transcript_processing.py에서 받은 데이터

Output:
    - VectorDB에 저장된 데이터

Guidance:
    - ID 부여 방식:
        - 서로 다른 youtube video, Docs 등 모든 source에 대해 global한 increasing count를 사용
        - 형식: {source_identifier}__{global_id}
        - 예시: Docs1__id1, Docs2__id2, youtube_video5__id3, Docs1__id4

    - Debugging 시:
        - 개별 source별로 debugging이 필요한 경우, source identifier로 filtering
        - 형식: Docs{num} 혹은 youtube_video{num}
        - Filtering 후 index reordering을 통해 debugging 수행
"""

import os
import json
from pinecone import Pinecone, ServerlessSpec
import dotenv

dotenv.load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_HOST = os.getenv("PINECONE_HOST")

# === File path Configuration ===

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

import sys
sys.path.append(parent_dir)
from utils.file_path_reader import load_video_config, file_loader
from utils.Pinecone_connection import get_index_host_mapping
from Youtube_tool.ID_extraction import extract_video_id

INPUT_FILE_PATH = os.path.join(parent_dir, "data", "results", "transcript_processing")
INPUT_FILE_NAME = "vectorDB_upsert_data"
INPUT_FILE_EXTENSION = "json"
INPUT_FILE_PATH_WITH_NAME = os.path.join(INPUT_FILE_PATH, INPUT_FILE_NAME)

# === Connect to VectorDB ===
def connect_to_Pinecone(api_key:str=PINECONE_API_KEY) -> Pinecone: # Level 1 (Pinecone Level)
    """
    Input: api_key type
        - example: PINECONE_API_KEY

    Output: Pinecone type
        - example: Pinecone(api_key=PINECONE_API_KEY)
    """
    return Pinecone(api_key=api_key)

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

def check_vector_id_existence(pc_index:"Pinecone.Index", namespace:str, vector_id_list:list[str]) -> bool:
    """
    Check vector id existence
    Input: pc_index, namespace, vector_id_list
        - pc_index: Pinecone.Index(host=PINECONE_HOST)
        - namespace: "namespace"
        - vector_id_list: ["vec1", "vec2", ...]

    Output: 
        - example: True
    
    Similar with SELECT in SQL: SELECT * FROM table WHERE id IN (vec1, vec2, ...)
    """
    if namespace in pc_index.describe_index_stats()['namespaces']:
        return bool(pc_index.fetch(ids=vector_id_list, namespace=namespace).vectors)
    else:
        return False

def get_namespace_len(pc_index:"Pinecone.Index", namespace:str) -> int: # Level 3 (namespace Level)
    """
    Get namespace length
    Input: pc_index, namespace
        - pc_index: Pinecone.Index(host=PINECONE_HOST)
        - namespace: "namespace"
    
    Output: int type
        - example: 2
    """
    exist = bool(pc_index.describe_index_stats()["namespaces"])
    if exist:
        return pc_index.describe_index_stats()["namespaces"][namespace]["vector_count"]
    else:
        return 0

def get_vector_data_samples(pc_index:"Pinecone.Index", ids:list[str], namespace:str) -> list[dict]: # Level 3 (namespace Level)
    """
    Get vector data of sample data
    Input: pc_index, ids, namespace
        - pc_index: Pinecone.Index(host=PINECONE_HOST)
        - ids: list[str] type
            - example: ["vec1", "vec2", ...]
        - namespace: "namespace"
    
    Output: FetchResponse type
        - example: FetchResponse(namespace="namespace", vectors=[{"id": "vec1", "values": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1], "metadata": {"genre": "comedy", "year": 2020}}, {"id": "vec2", "values": [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2], "metadata": {"genre": "documentary", "year": 2019}}])
    """
    return pc_index.fetch(ids=ids, namespace=namespace).vectors

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

def records_id_sampling(pc_index:"Pinecone.Index", limit:int, namespace:str) -> list[str]: # Level 3 (namespace Level)
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

def upsert_data(pc_index:"Pinecone.Index", vectors:list[dict], namespace:str) -> None: # Level 2 (Index Level)
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
    vector_exist = check_vector_id_existence(pc_index=pc_index, namespace=namespace, vector_id_list=list(map(lambda x: x["id"], vectors)))
    if vector_exist:
        print("The vector already exist!! all upsert has been canceled")
    else:
        pc_index.upsert(namespace, vectors)

def upsert_records(dict_of_pc_index:dict[str, "Pinecone.Index"], all_records:dict[str, list[dict]], video_config:dict, batch_size:int=96) -> None: # Level 2 (Index Level)
    """
    It's for integrated model
    Input: dict_of_pc_index, records, video_config
        - dict_of_pc_index: dict[str, Pinecone.Index(host=PINECONE_HOST)]
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
    video_config_keys_to_id = {extract_video_id(video_url): video_config[video_url] for video_url in video_config.keys()}

    for video_id, records in all_records.items():
        video_config_data = video_config_keys_to_id[video_id]
        index_name = video_config_data["index_name"]
        namespace = video_config_data["namespace"]
        pc_index = dict_of_pc_index[index_name]

        # Check only first and last record to avoid 414 error
        # If these exist, assume entire batch was already uploaded
        sample_ids = [records[0]["id"], records[-1]["id"]] if len(records) > 1 else [records[0]["id"]]
        record_exist = check_vector_id_existence(pc_index=pc_index, namespace=namespace, vector_id_list=sample_ids)

        batch_split_list = [records[i:i+batch_size] for i in range(0, len(records), batch_size)]
        if record_exist:
            print(f"Records for video {video_id} already exist (checked first/last). Skipping upsert.")
        else:
            print(f"Upserting {len(records)} records for video {video_id} in {len(batch_split_list)} batches...")
            for idx, batch in enumerate(batch_split_list, 1):
                pc_index.upsert_records(namespace, batch)
                print(f"  Batch {idx}/{len(batch_split_list)} uploaded ({len(batch)} records)")

def delete_vector_data(pc_index:"Pinecone.Index", namespace:str, vector_id_list:list[str]=[]) -> None:
    """
    Delete vector id
    Input: pc, namespace, vector_id_list
        - pc: Pinecone(api_key=PINECONE_API_KEY)
        - namespace: "namespace"
        - vector_id_list: ["vec1", "vec2", ...]
    """
    vector_exist = check_vector_id_existence(pc_index=pc_index, namespace=namespace, vector_id_list=vector_id_list)
    if vector_exist:
        pc_index.delete(ids=vector_id_list, namespace=namespace)
    else:
        print("The vector id does not exist!! all delete has been canceled")

def main():
    global INPUT_FILE_PATH, INPUT_FILE_NAME, INPUT_FILE_EXTENSION
    video_config = load_video_config()

    pc = connect_to_Pinecone(api_key=PINECONE_API_KEY)
    index_host_mapping:dict[str, str] = get_index_host_mapping(pc)
    dict_of_pc_index = {}
    for index_name, host in index_host_mapping.items():
        dict_of_pc_index[index_name] = connect_to_Index(pc=pc, host=host)
    """
    dict_of_pc_index == {
        "developer-quickstart-py": Pinecone.Index(host="developer-quickstart-py-nibcub6.svc.aped-4627-b74a.pinecone.io"),
        "another-index": Pinecone.Index(host="another-index-xyz123.svc.aped-4627-b74a.pinecone.io")
    }
    """

    transcript_data = file_loader(file_path=INPUT_FILE_PATH, file_name=INPUT_FILE_NAME, file_extension=INPUT_FILE_EXTENSION)
    if transcript_data is None:
        raise ValueError("Transcript data is not loaded")


    upsert_records(dict_of_pc_index=dict_of_pc_index, all_records=transcript_data, video_config=video_config, batch_size=96)
    print(f"{len(transcript_data)} records has been upserted! Done!")

if __name__ == "__main__":
    main()