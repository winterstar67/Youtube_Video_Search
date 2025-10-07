"""
Order in pipeline: Fourth (4)

Function:
    - Query를 받으면, 지정한 index의 namespace 내에서  데이터를 찾음

lexical search 도 있음을 고려해야 함.
- 나중에 수정할 수 있음.
- 혹은 Lexical_search.py 파일을 만들어서 따로 관리할 수 있음.

Input:
    - 사용자의 Query text

Output:

Function:
- Pinecone의 semantic search의 함수는 종류가 2개가 있다.
    - index.query: embedding vector를 받아서 사용하는 경우로, index가 integrated model이 아닌 경우에 사용한다.
    - index.search: text를 받아서 사용하는 경우로, index가 integrated model인 경우에 사용한다.
- 어떤 method로 similarity를 계산하는 지는 index 생성 단계에서 지정된다고 함.

"""

### === Configuration ===
import os
import dotenv
from pinecone import Pinecone
import json
import sys

dotenv.load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_HOST = os.getenv("PINECONE_HOST")



### === File path Configuration ===
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

sys.path.append(parent_dir)
from utils import file_path_reader, Pinecone_connection

INPUT_FILE_PATH = os.path.join(parent_dir, "data", "external_data")
INPUT_FILE_NAME = "query.json"
INPUT_FILE_PATH_WITH_NAME = os.path.join(INPUT_FILE_PATH, INPUT_FILE_NAME)

OUTPUT_FILE_PATH = os.path.join(parent_dir, "data", "results")
OUTPUT_FILE_NAME = "semantic_search_results"
OUTPUT_FILE_EXTENSION = "pkl"

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

### === Function ===

def load_query(input_file_path:str=INPUT_FILE_PATH_WITH_NAME) -> dict:
    """
    Load query from file
    Input: input_file_path
        - example: "../data/external_data/query.json"
    """
    with open(input_file_path, "r") as f:
        query = json.load(f)
    return query

def save_result_to_file(result:list[dict], output_file_path:str, output_file_name:str, output_file_extension:str) -> None:
    """
    Save result to file
    Input: result
        - example: [{"id": "1", "text": "Hello, world!"}]
    Input: output_file_path, output_file_name, output_file_extension
        - example: "../data/results/semantic_search_results.json"

    Output: None
    """
    backup_file_path = file_path_reader.backup_file_path_reader(output_file_name=output_file_name, output_file_extension=output_file_extension)
    output_file_path_with_name = output_file_path + "/" + output_file_name + "." + output_file_extension
    with open(output_file_path_with_name, "w") as f:
        json.dump(result, f)
    with open(backup_file_path, "w") as f:
        json.dump(result, f)

def semantic_search_with_text(query:dict, pc_index:Pinecone.Index, namespace:str, config:dict, rerank:bool=False) -> list[dict]:
    """
    It's for semantic search with text - which means it's integrated index
    Input: query, pc_index, namespace, config
        - query: dict
        - pc_index: Pinecone.Index
        - namespace: str
        - config: dict

    Output: results
        - example: [{"id": "1", "text": "Hello, world!"}]
    """
    if rerank:
        results = pc_index.search(
            namespace=namespace,
            query=query,
            rerank={
                "model": "bge-reranker-v2-m3",
                "top_n": 5,
                "rank_fields": ["chunk_text"]
            },
            fields=["chunk_text", "metadata"]
        ).to_dict()
    else:
        results = pc_index.search(
            namespace=namespace,
            query=query
        ).to_dict()
    return results

def main():
    query = load_query(input_file_path=INPUT_FILE_PATH_WITH_NAME)
    pc = Pinecone_connection.connect_to_Pinecone(api_key=PINECONE_API_KEY)
    pc_index = Pinecone_connection.connect_to_Index(pc=pc, host=PINECONE_HOST)
    results = semantic_search_with_text(query=query, pc_index=pc_index, namespace=config["namespace"], config=config, rerank=True)
    print("results: ", results)
    save_result_to_file(result=results, output_file_path=OUTPUT_FILE_PATH, output_file_name=OUTPUT_FILE_NAME, output_file_extension=OUTPUT_FILE_EXTENSION)

if __name__ == "__main__":
    main()
    print("Done!")