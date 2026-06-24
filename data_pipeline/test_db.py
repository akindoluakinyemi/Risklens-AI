import os
from sqlalchemy import create_engine
from dotenv import load_dotenv
import pandas as pd

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

query = """
SELECT * FROM asset_prices LIMIT 10;
"""

query2 ="""
SELECT symbol, COUNT(*) as observations FROM asset_prices GROUP BY symbol ORDER BY symbol
"""
df = pd.read_sql(query, engine)
print(df)

df = pd.read_sql(query2, engine)
print(df)