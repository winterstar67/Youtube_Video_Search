"""
Airflow DAG for YouTube Video Processing Pipeline

Pipeline:
1. Extract YouTube transcription (Youtube_transcription.py)
2. Process transcript into sentences (transcript_processing.py)
3. Store processed data in VectorDB (Store_on_VectorDB.py)

Schedule: Daily at 2 AM KST
"""

import os
import sys
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash_operator import BashOperator

# Add project root to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Import project modules
from src import Youtube_transcription, transcript_processing, Store_on_VectorDB

# Default arguments for DAG
default_args = {
    'owner': 'youtube_pipeline',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG
dag = DAG(
    'youtube_video_processing_pipeline',
    default_args=default_args,
    description='YouTube video transcription and VectorDB storage pipeline',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    catchup=False,
    tags=['youtube', 'transcription', 'vectordb'],
)

# Task 1: Extract YouTube Transcription
def extract_transcription(**context):
    """
    Extract transcription from YouTube videos
    Input: video_link_target.yaml
    Output: Youtube_transcription.pkl
    """
    try:
        print("Starting YouTube transcription extraction...")
        result = Youtube_transcription.get_transcription()

        if result:
            video_count = len(result)
            print(f"Successfully extracted transcription for {video_count} videos")
            context['ti'].xcom_push(key='transcription_count', value=video_count)
            return video_count
        else:
            raise ValueError("No transcription extracted")
    except Exception as e:
        print(f"Error in transcription extraction: {str(e)}")
        raise

task_extract_transcription = PythonOperator(
    task_id='extract_youtube_transcription',
    python_callable=extract_transcription,
    provide_context=True,
    dag=dag,
)

# Task 2: Process Transcripts
def process_transcripts(**context):
    """
    Process transcripts into sentences with metadata
    Input: Youtube_transcription.pkl
    Output: transcript_by_sentence.json, vectorDB_upsert_data.json
    """
    try:
        print("Starting transcript processing...")
        result = transcript_processing.main()

        if result:
            record_count = len(result)
            print(f"Successfully processed {record_count} records")
            context['ti'].xcom_push(key='processed_records', value=record_count)
            return record_count
        else:
            raise ValueError("No records processed")
    except Exception as e:
        print(f"Error in transcript processing: {str(e)}")
        raise

task_process_transcripts = PythonOperator(
    task_id='process_transcripts',
    python_callable=process_transcripts,
    provide_context=True,
    dag=dag,
)

# Task 3: Store in VectorDB
def store_in_vectordb(**context):
    """
    Store processed data in Pinecone VectorDB
    Input: vectorDB_upsert_data.json
    Output: Data stored in Pinecone
    """
    try:
        print("Starting VectorDB storage...")
        Store_on_VectorDB.main()

        # Get previous task's record count
        processed_records = context['ti'].xcom_pull(
            task_ids='process_transcripts',
            key='processed_records'
        )
        print(f"Successfully stored {processed_records} records in VectorDB")
        return processed_records
    except Exception as e:
        print(f"Error in VectorDB storage: {str(e)}")
        raise

task_store_vectordb = PythonOperator(
    task_id='store_in_vectordb',
    python_callable=store_in_vectordb,
    provide_context=True,
    dag=dag,
)

# Task 4: Cleanup and Validation
def validate_pipeline(**context):
    """
    Validate that all pipeline steps completed successfully
    """
    transcription_count = context['ti'].xcom_pull(
        task_ids='extract_youtube_transcription',
        key='transcription_count'
    )
    processed_records = context['ti'].xcom_pull(
        task_ids='process_transcripts',
        key='processed_records'
    )

    print("=" * 50)
    print("Pipeline Validation Summary")
    print("=" * 50)
    print(f"Videos transcribed: {transcription_count}")
    print(f"Records processed: {processed_records}")
    print(f"Status: SUCCESS")
    print("=" * 50)

    return {
        'status': 'SUCCESS',
        'transcription_count': transcription_count,
        'processed_records': processed_records,
        'completion_time': datetime.now().isoformat()
    }

task_validate = PythonOperator(
    task_id='validate_pipeline',
    python_callable=validate_pipeline,
    provide_context=True,
    dag=dag,
)

# Set task dependencies
task_extract_transcription >> task_process_transcripts >> task_store_vectordb >> task_validate

# Optional: Add a task to send notification on completion
def send_completion_notification(**context):
    """
    Send notification when pipeline completes
    """
    validation_result = context['ti'].xcom_pull(task_ids='validate_pipeline')
    print(f"Pipeline completed successfully: {validation_result}")
    return validation_result

task_notify = PythonOperator(
    task_id='send_notification',
    python_callable=send_completion_notification,
    provide_context=True,
    dag=dag,
)

task_validate >> task_notify
