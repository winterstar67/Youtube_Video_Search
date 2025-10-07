import os
from pinecone import Pinecone, ServerlessSpec
import dotenv

dotenv.load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_HOST = os.getenv("PINECONE_HOST")

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