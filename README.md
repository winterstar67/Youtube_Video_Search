# YouTube Video Search (RAG Pipeline)

This project builds a YouTube transcript-based retrieval pipeline:

1. Collect transcripts + video metadata from YouTube
2. Split and preprocess transcript text into sentence chunks
3. Save chunks into Pinecone VectorDB
4. Retrieve relevant chunks with semantic search

## Project Structure

```text
src/
  Youtube_transcription.py
  transcript_processing.py
  Store_on_VectorDB.py
  Semantic_search.py
  gpt_based_weired_word_sensor.py
  Youtube_tool/
    ID_extraction.py
    Youtube_Collection.py
utils/
  file_path_reader.py
  Pinecone_connection.py
  text_pattern_filter.py
data/
  raw_data/      # user-provided inputs (not tracked)
  results/       # pipeline outputs
```

## Prerequisites

- Python 3.10+
- Pinecone account + index host
- YouTube Data API key
- (Optional) OpenAI API key for `gpt_based_weired_word_sensor.py`

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Required Input Data (before running)

Create these files under `data/raw_data/`:

1. `video_link_target.yaml`
2. `transcript_processing_config.json`
3. (Optional for `Semantic_search.py`) `query.json`

### 1) `video_link_target.yaml` example

```yaml
https://www.youtube.com/watch?v=VIDEO_ID:
  index_name: developer-quickstart-py
  namespace: Video_RAG
  cloud: aws
  region: us-east-1
  embed:
    model: llama-text-embed-v2
    field_map:
      text: chunk_text
  Author: ""
  Comment: ""
```

### 2) `transcript_processing_config.json` example

```json
{
  "SaT_model": "sat-1l-sm",
  "SaT_threshold": 0.5,
  "concat_length": 3,
  "use_gpu": "False"
}
```

### 3) `query.json` example

```json
{
  "inputs": {"text": "What kind of content has been covered?"},
  "top_k": 5
}
```

## Environment Variables

Create `.env` with:

```env
YOUTUBE_API_KEY=
PINECONE_API_KEY=
PINECONE_HOST=
OPENAI_API_KEY=
```

## Run Pipeline

```bash
python src/Youtube_transcription.py
python src/transcript_processing.py
python src/Store_on_VectorDB.py
```

## Retrieve

Use Pinecone integrated search (`index.search`) with your namespace.

Note: `src/Semantic_search.py` currently contains known issues and may require fixes before direct use.

## Metadata Time Extraction (`start`, `end`)

Time metadata is generated in `src/transcript_processing.py`:

- `attach_start_end(...)` maps sentence chunks to original transcript snippets.
- `start` comes from first matched snippet start.
- `end` is computed as `snippet.start + snippet.duration`.
- `seconds_to_hms(...)` converts values to `HH:MM:SS`.
- Final record metadata is saved and upserted to Pinecone in `Store_on_VectorDB.py`.

## Performance Note (SaT)

`SaT` sentence splitting can be computationally heavy for large transcript sets.  
If local GPU is limited, run this stage in a GPU environment (for example, Google Colab).

## Security Note

Do not commit `.env` or any API keys to Git.

## License

- Your project code: MIT License (see `LICENSE`)
- Third-party dependency licenses and notices: see `THIRD_PARTY_NOTICES.md`

