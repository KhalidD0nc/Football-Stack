import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def main():
    # Load environment variables from .env
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)

    gcs_bucket = os.environ.get("GCS_BUCKET")
    gcs_project = os.environ.get("GCS_PROJECT")

    if not gcs_bucket:
        print("Error: GCS_BUCKET environment variable is not set. Please check your .env file.")
        sys.exit(1)

    if not gcs_project:
        print("Error: GCS_PROJECT environment variable is not set. Please check your .env file.")
        sys.exit(1)

    print(f"Initializing BigQuery DDL for Project: {gcs_project}, Bucket: {gcs_bucket}")

    try:
        from google.cloud import bigquery
    except ImportError:
        print("Error: google-cloud-bigquery library is not installed.")
        print("Please run: pip install google-cloud-bigquery")
        sys.exit(1)

    # Initialize BigQuery Client
    client = bigquery.Client(project=gcs_project)

    # Read the DDL script
    ddl_path = Path(__file__).resolve().parent.parent / "sql" / "bigquery_ddl.sql"
    if not ddl_path.exists():
        print(f"Error: Could not find DDL file at {ddl_path}")
        sys.exit(1)

    with open(ddl_path, "r", encoding="utf-8") as f:
        ddl_content = f.read()

    # Replace the variable placeholder with the actual bucket name
    ddl_content = ddl_content.replace("${GCS_BUCKET}", gcs_bucket)

    import re
    # To properly split by semicolon without breaking strings or comments:
    # We can just iterate over the script and split, but skipping semicolons inside block comments
    # A safer approach for BigQuery is to send the entire script as a single job script.
    
    # Execute the DDL script as a single query
    print("Executing DDL script...")
    
    job_config = bigquery.QueryJobConfig()
    try:
        query_job = client.query(ddl_content, job_config=job_config)
        query_job.result()  # Wait for the job to complete
        print("Successfully executed DDL script.")
    except Exception as e:
        print(f"\nError executing DDL:")
        print(e)
        sys.exit(1)

    print("BigQuery initialization complete!")

if __name__ == "__main__":
    main()
