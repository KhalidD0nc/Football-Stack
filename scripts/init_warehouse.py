import argparse
import logging
import os
import sys

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def parse_args():
    parser = argparse.ArgumentParser(description="Initialize Data Warehouse Infrastructure.")
    parser.add_argument("--test", action="store_true", help="Initialize the TEST database instead of production.")
    return parser.parse_args()

def init_infrastructure(is_test: bool):
    """
    Connect to Snowflake using the WAREHOUSE_URI and issue raw DDL commands
    to create the Databases and Schemas if they don't exist.
    """
    load_dotenv()
    
    # Select the URI based on the --test flag
    env_var = "WAREHOUSE_URI_TEST" if is_test else "WAREHOUSE_URI"
    uri = os.getenv(env_var)
    if not uri:
        logger.error(f"Missing environment variable: {env_var}")
        sys.exit(1)

    # We want to connect at the Account level to create DBs, so we strip the DB and Schema from the URI.
    # The URI format is: dialect://user:pass@host/DATABASE/SCHEMA?params
    
    # This is a slightly hacky but effective way to ensure we don't connect to a DB that doesn't exist yet.
    # We replace the hardcoded database with 'SNOWFLAKE' (which always exists).
    
    base_uri = getattr(uri, 'replace', lambda x,y: uri)(f"/LEAGUES_DATA_TEST/STAGING", "/SNOWFLAKE/PUBLIC")
    base_uri = base_uri.replace(f"/LEAGUES_DATA/STAGING", "/SNOWFLAKE/PUBLIC")
    
    target_db = "LEAGUES_DATA_TEST" if is_test else "LEAGUES_DATA"

    try:
        logger.info(f"Connecting to Warehouse to initialize [{target_db}]...")
        engine = create_engine(base_uri)
        
        with engine.begin() as conn:
            # 1. Create the Database
            logger.info(f"Creating Database: {target_db}")
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {target_db}"))
            
            # 2. Use the Database we just created or verified
            conn.execute(text(f"USE DATABASE {target_db}"))
            
            # 3. Create only the landing Schemas that the Python pipeline needs.
            # (dbt automatically handles creating SILVER, GOLD, PLATINUM, etc., when it builds models)
            schemas = ["STAGING", "RAW"]
            for schema in schemas:
                logger.info(f"Creating Schema: {schema}")
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                
        logger.info("Infrastructure initialization complete! 🚀")

    except ImportError:
        logger.error(
            "Missing required SQLAlchemy drivers. "
            "Run: pip install sqlalchemy snowflake-sqlalchemy"
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to initialize infrastructure: {e}")
        sys.exit(1)


if __name__ == "__main__":
    args = parse_args()
    init_infrastructure(args.test)
