import os, re, sqlparse
from typing import Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from openai import OpenAI
from db import fetch_df

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ALLOWED = {
    "dim_date": ["date_key","year","quarter","month","day","iso_week"],
    "dim_customer": ["customer_id","email","signup_date","country","segment"],
    "dim_product": ["product_id","sku","name","category","unit_cost"],
    "fact_orders": ["order_id","order_ts","date_key","customer_id","status","subtotal","discount","tax","shipping","total"],
    "fact_order_items": ["order_item_id","order_id","product_id","quantity","unit_price","line_total"],
    "fact_events": ["event_id","event_ts","date_key","customer_id","event_name","event_value","meta"],
    "v_daily_revenue": ["date_key","revenue","refunds","orders_paid","orders_all"],
    "v_revenue_rolling_7d": ["date_key","revenue","revenue_rolling_7d"],
    "v_top_products_30d": ["product_id","name","category","units","sales"],
    "v_retention_cohorts": ["cohort_month","active_month","active_customers"],
    "mv_daily_metrics": ["date_key","revenue","refunds","orders_paid","paying_customers"]
}

SCHEMA_HINT = "\n".join(
    f"- {t}({', '.join(cols)})" for t, cols in ALLOWED.items()
)

class SqlAnswer(BaseModel):
    sql: str = Field(..., description="A single SELECT statement with named parameters where sensible.")
    rationale: str

BLOCK = re.compile(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|GRANT|REVOKE|CALL|CREATE)\b", re.I)

def is_safe_select(sql: str) -> bool:
    parsed = sqlparse.parse(sql)
    if len(parsed) != 1:
        return False
    stmt = parsed[0]
    if stmt.get_type() != "SELECT":
        return False
    if BLOCK.search(sql):
        return False
    # Only allowed tables
    lower = sql.lower()
    for word in re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", lower):
        if word in {"select","from","where","join","on","and","or","case","when","then","else","end",
                    "group","by","order","limit","offset","asc","desc","having","as","distinct",
                    "sum","count","avg","min","max","date_trunc","coalesce","filter","over","rows","between","preceding","current","row","jsonb","extract"}:
            continue
        # If it matches a table name, ensure it's allowed (columns are not strictly enforced here)
        if word in ALLOWED.keys():
            continue
    return True

def ensure_limit(sql: str, default_limit: int = 500) -> str:
    if re.search(r"\blimit\b", sql, re.I):
        return sql
    return sql + f"\nLIMIT {default_limit}"

SYSTEM = f"""You are a data analyst that writes safe PostgreSQL SELECT queries only.
Use ONLY these relations and columns:
{SCHEMA_HINT}
Rules:
- Single SELECT statement only. No CTEs with write ops. No DDL/DML.
- Prefer existing views when they fit the question.
- Use parameter names like :start_date, :end_date, :limit when appropriate.
Return JSON with fields: sql, rationale."""

def ask(question: str, params: dict | None = None):
    # You can swap model to gpt-4.1, o4-mini, etc.
    msg = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {"role":"system","content":SYSTEM},
            {"role":"user","content":question}
        ],
        response_format={"type": "json_schema", "json_schema": {
            "name": "sql_answer",
            "schema": {"type":"object","required":["sql","rationale"],
                       "properties":{"sql":{"type":"string"},
                                     "rationale":{"type":"string"}}},
            "strict": True
        }}
    )
    out = SqlAnswer.model_validate_json(msg.output[0].content[0].text)
    sql = ensure_limit(out.sql.strip())
    if not is_safe_select(sql):
        raise ValueError("Unsafe or invalid SQL produced.")
    return fetch_df(sql, params or {}), sql, out.rationale
