from pathlib import Path
from db import fetch_df

SQL_DIR = Path(__file__).parent / "analytics_sql"

def _read_sql(name: str) -> str:
    return (SQL_DIR / name).read_text()

def daily_kpis(start_date: str, end_date: str):
    return fetch_df(_read_sql("daily_kpis.sql"), {"start_date": start_date, "end_date": end_date})

def top_products_30d(limit: int = 20):
    return fetch_df(_read_sql("top_products_30d.sql"), {"limit": limit})

def revenue_rolling_7d(start_date: str, end_date: str):
    return fetch_df(_read_sql("revenue_rolling_7d.sql"), {"start_date": start_date, "end_date": end_date})

def retention_cohorts(cohort_start: str, cohort_end: str):
    return fetch_df(_read_sql("retention_cohorts.sql"), {"cohort_start": cohort_start, "cohort_end": cohort_end})
