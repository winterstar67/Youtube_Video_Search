"""
FastAPI Application for YouTube Video Search and Storage

Endpoints:
1. /search - Search functionality using semantic search
2. /store - Store YouTube video transcripts in VectorDB
"""

import os
import sys
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
import json
import yaml

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import project modules
from src import Semantic_search, Youtube_transcription, transcript_processing, Store_on_VectorDB
from utils.Pinecone_connection import connect_to_Pinecone, connect_to_Index
from utils.file_path_reader import save_result_to_file
import dotenv

dotenv.load_dotenv()

app = FastAPI(title="YouTube Video Search & Storage System")

# Setup templates
templates = Jinja2Templates(directory=os.path.join(current_dir, "templates"))

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(current_dir, "static")), name="static")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_HOST = os.getenv("PINECONE_HOST")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with links to search and store functionalities"""
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    """Search page"""
    return templates.TemplateResponse("search.html", {"request": request})

@app.post("/search/execute")
async def execute_search(
    query: str = Form(...),
    index_name: str = Form("developer-quickstart-py"),
    namespace: str = Form("test"),
    rerank: bool = Form(True)
):
    """
    Execute semantic search

    Parameters:
    - query: Search query text
    - index_name: Pinecone index name
    - namespace: Pinecone namespace
    - rerank: Whether to use reranking (default: True)
    """
    try:
        # Connect to Pinecone
        pc = connect_to_Pinecone(api_key=PINECONE_API_KEY)
        pc_index = connect_to_Index(pc=pc, host=PINECONE_HOST)

        # Configure search
        config = {
            "index_name": index_name,
            "namespace": namespace,
            "embed": {
                "model": "llama-text-embed-v2",
                "field_map": {"text": "chunk_text"}
            }
        }

        # Execute search
        results = Semantic_search.semantic_search_with_text(
            query=query,
            pc_index=pc_index,
            namespace=namespace,
            config=config,
            rerank=rerank
        )

        # Save results
        output_file_path = os.path.join(parent_dir, "data", "results")
        output_file_name = f"semantic_search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        output_file_extension = "json"

        save_result_to_file(
            result=results,
            file_path=output_file_path,
            file_name=output_file_name,
            file_extension=output_file_extension
        )

        return JSONResponse(content={
            "status": "success",
            "message": "Search completed successfully",
            "results": results,
            "saved_to": f"{output_file_name}.{output_file_extension}"
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e)
            }
        )

@app.get("/store", response_class=HTMLResponse)
async def store_page(request: Request):
    """Store page"""
    return templates.TemplateResponse("store.html", {"request": request})

@app.post("/store/execute")
async def execute_store(
    video_url: str = Form(...),
    author: str = Form(""),
    comment: str = Form("")
):
    """
    Store YouTube video transcript in VectorDB

    Parameters:
    - video_url: YouTube video URL
    - author: Author/Source name (optional)
    - comment: Additional comment (optional)

    Pipeline: Youtube_transcription -> transcript_processing -> Store_on_VectorDB
    """
    try:
        # Step 1: Create temporary YAML file with video URL
        temp_yaml_path = os.path.join(parent_dir, "data", "external_data", "video_link_target.yaml")

        # Read existing URLs if file exists
        existing_urls = []
        if os.path.exists(temp_yaml_path):
            with open(temp_yaml_path, "r") as f:
                existing_data = yaml.safe_load(f)
                if existing_data and "target_video_link" in existing_data:
                    existing_urls = existing_data["target_video_link"]

        # Add new URL if not already present
        if video_url not in existing_urls:
            existing_urls.append(video_url)
            with open(temp_yaml_path, "w") as f:
                yaml.dump({"target_video_link": existing_urls}, f)

        # Step 2: Extract transcription
        transcription_result = Youtube_transcription.get_transcription(file_path=temp_yaml_path)

        if not transcription_result:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Failed to extract transcription"
                }
            )

        # Step 3: Update config with Author and Comment
        transcript_processing.config["Author"] = author
        transcript_processing.config["Comment"] = comment

        # Process transcripts
        processed_data = transcript_processing.main()

        # Step 4: Store in VectorDB
        Store_on_VectorDB.main()

        return JSONResponse(content={
            "status": "success",
            "message": "Video transcript stored successfully in VectorDB",
            "video_url": video_url,
            "author": author,
            "comment": comment,
            "records_processed": len(processed_data) if processed_data else 0
        })

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "details": str(type(e).__name__)
            }
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
