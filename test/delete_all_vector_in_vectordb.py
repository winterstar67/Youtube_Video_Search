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

# INPUT_FILE_PATH = os.path.join(parent_dir, "data", "results")
# INPUT_FILE_NAME = "vectorDB_upsert_data.json"
# INPUT_FILE_PATH_WITH_NAME = os.path.join(INPUT_FILE_PATH, INPUT_FILE_NAME)
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

def delete_vector_data(pc_index:"Pinecone.Index", namespace:str) -> None:
    """
    Delete vector id
    Input: pc, namespace, vector_id_list
        - pc: Pinecone(api_key=PINECONE_API_KEY)
        - namespace: "namespace"
        - vector_id_list: ["vec1", "vec2", ...]
    """
    pc_index.delete()
 
def main():
    pc = connect_to_Pinecone()
    pc_index = connect_to_Index(pc)

if __name__ == "__main__":
    main()