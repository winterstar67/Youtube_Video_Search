import os
from pinecone import Pinecone, ServerlessSpec
import dotenv

dotenv.load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

def connect_to_Pinecone(api_key:str=PINECONE_API_KEY) -> Pinecone: # Level 1 (Pinecone Level)
    """
    Input: api_key type
        - example: PINECONE_API_KEY

    Output: Pinecone type
        - example: Pinecone(api_key=PINECONE_API_KEY)
    """
    return Pinecone(api_key=api_key)

def connect_to_Index(pc:Pinecone, host:str) -> "Pinecone.Index": # Level 2 (Index Level)
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

def get_index_host_mapping(pc:Pinecone) -> dict[str, str]:
    """
    Get mapping of index names to their hosts

    Note: If duplicate index names exist (which shouldn't happen in Pinecone),
    only the last occurrence will be kept in the dictionary.

    Input: pc
        - pc: Pinecone(api_key=PINECONE_API_KEY)

    Output: dict[str, str]
        - example: {
            "developer-quickstart-py": "developer-quickstart-py-nibcub6.svc.aped-4627-b74a.pinecone.io",
            "another-index": "another-index-xyz123.svc.aped-4627-b74a.pinecone.io",
            ...
          }
    """
    indexes = pc.list_indexes()
    index_host_mapping = {}

    for index in indexes:
        index_name = index['name']
        index_host = index['host']

        # Skip if duplicate key already exists (dictionary comprehension would overwrite anyway)
        if index_name in index_host_mapping:
            print(f"Warning: Duplicate index name '{index_name}' found. Skipping duplicate.")
            continue

        index_host_mapping[index_name] = index_host

    return index_host_mapping