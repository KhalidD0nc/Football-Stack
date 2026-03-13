import os
import polars as pl
from dotenv import load_dotenv

load_dotenv()
uri = os.environ.get("WAREHOUSE_URI_TEST")
if uri:
    try:
        # Just query the information schema
        res = pl.read_database("SHOW SCHEMAS IN DATABASE LEAGUES_DATA_TEST", connection=uri)
        print("Schemas in LEAGUES_DATA_TEST:")
        print(res)
    except Exception as e:
        print("Error showing schemas in LEAGUES_DATA_TEST:", e)
    
    try:
        res2 = pl.read_database("SELECT CURRENT_ROLE(), CURRENT_DATABASE(), CURRENT_SCHEMA()", connection=uri)
        print("Current Context:", res2)
    except Exception as e:
         print("Error getting context:", e)
