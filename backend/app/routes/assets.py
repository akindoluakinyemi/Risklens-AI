import os
import pandas as pd
from sqlalchemy import create_engine
from fastapi import APIRouter
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

router = APIRouter(prefix="/assets", tags=["Assets"])

@router.get("/")
def get_assets():
    query = """
        SELECT 
            symbol, 
            COUNT(*) as observations,
            MIN(date) as start_date,
            MAX(date) as end_date
        FROM asset_prices
        GROUP BY symbol
        ORDER BY symbol;
    """
    df = pd.read_sql(query, engine)
    return df.to_dict(orient="records")