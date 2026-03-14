import argparse
import logging
import os
import sys

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Download tables from the silver schema as CSV.")
    parser.add_argument("--test", action="store_true", help="Download from the TEST database instead of production.")
    parser.add_argument("--output-dir", type=str, default="./exports", help="Directory to save the CSV files.")
    return parser.parse_args()

def download_silver_tables(is_test: bool, output_dir: str):
    load_dotenv()
    
    # Select the URI based on the --test flag
    env_var = "WAREHOUSE_URI_TEST" if is_test else "WAREHOUSE_URI"
    uri = os.getenv(env_var)
    if not uri:
        logger.error(f"Missing environment variable: {env_var}")
        sys.exit(1)

    target_db = "LEAGUES_DATA_TEST" if is_test else "LEAGUES_DATA"

    # Make sure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    try:
        logger.info(f"Connecting to Warehouse [{target_db}]...")
        engine = create_engine(uri)
        
        with engine.connect() as conn:
            # Query the information_schema to get all tables in the SILVER schema
            query = text(f"""
                SELECT TABLE_NAME 
                FROM {target_db}.INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_SCHEMA = 'SILVER' AND TABLE_TYPE = 'BASE TABLE'
            """)
            
            result = conn.execute(query)
            tables = [row[0] for row in result]
            
            if not tables:
                logger.warning(f"No tables found in the SILVER schema of {target_db}.")
                return

            logger.info(f"Found {len(tables)} tables in SILVER schema. Starting download...")
            
            for table in tables:
                # Remove 'SILVER_' prefix from the table name
                clean_name = table.lower()
                if clean_name.startswith("silver_"):
                    clean_name = clean_name[len("silver_"):]
                
                output_path = os.path.join(output_dir, f"{clean_name}.csv")
                
                logger.info(f"Downloading table '{table}' to '{output_path}'...")
                
                # Fetch data and save as CSV
                df = pd.read_sql(text(f"SELECT * FROM {target_db}.SILVER.{table}"), conn)
                df.to_csv(output_path, index=False)
                
                logger.info(f"Successfully saved {len(df)} rows to '{output_path}'.")
                
        logger.info(f"All downloads complete! Files saved in: {os.path.abspath(output_dir)}")

    except ImportError:
        logger.error(
            "Missing required packages. "
            "Ensure you have pandas, sqlalchemy, and snowflake-snowflake-sqlalchemy installed."
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to download tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    args = parse_args()
    download_silver_tables(args.test, args.output_dir)
