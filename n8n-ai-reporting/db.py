import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd

load_dotenv()
ENGINE = create_engine(os.getenv("DATABASE_URL"), pool_pre_ping=True)

def fetch_df(sql: str, params: dict | None = None) -> pd.DataFrame:
    with ENGINE.begin() as cxn:
        return pd.read_sql(text(sql), cxn, params=params or {})
