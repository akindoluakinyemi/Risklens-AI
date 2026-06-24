import os
import sys
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.models import AssetPrice
from backend.app.database import Base


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL is not set. Check your .env file.")


engine = create_engine(DATABASE_URL)


def load_market_data(csv_path: str = "market_data.csv") -> None:
    df = pd.read_csv(csv_path)

    df["date"] = pd.to_datetime(df["date"]).dt.date

    Base.metadata.create_all(bind=engine)

    df.to_sql(
        name=AssetPrice.__tablename__,
        con=engine,
        if_exists="append",
        index=False,
        method="multi"
    )

    print(f"Loaded {len(df)} rows into PostgreSQL.")


if __name__ == "__main__":
    load_market_data()