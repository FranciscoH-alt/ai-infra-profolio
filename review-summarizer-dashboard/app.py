import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler
import plotly.express as px
import plotly.graph_objects as go
import re
from pathlib import Path  # <-- added

st.set_page_config(page_title="Customer Review Summarizer", layout="wide")

@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["review_date"])
    df["review_text"] = df["review_text"].fillna("")
    return df

@st.cache_data
def compute_sentiment(texts: pd.Series) -> pd.DataFrame:
    analyzer = SentimentIntensityAnalyzer()
    scores = texts.apply(lambda t: analyzer.polarity_scores(str(t)))
    sdf = pd.DataFrame(list(scores))
    label = np.where(sdf["compound"] >= 0.2, "Positive",
                     np.where(sdf["compound"] <= -0.2, "Negative", "Neutral"))
    sdf["label"] = label
    return sdf

def top_terms(df: pd.DataFrame, n_terms: int = 12) -> pd.DataFrame:
    """Return top TF-IDF terms for the current dataframe slice."""
    texts = df["review_text"].fillna("")
    texts = texts.apply(lambda x: re.sub(r"[^A-Za-z0-9\s]", " ", x.lower()))
    vec = TfidfVectorizer(stop_words="english", max_features=5000, ngram_range=(1,2))
    X = vec.fit_transform(texts)
    mean_scores = np.asarray(X.mean(axis=0)).flatten()
    terms = np.array(vec.get_feature_names_out())
    idx = mean_scores.argsort()[::-1][:n_terms]
    return pd.DataFrame({"term": terms[idx], "score": mean_scores[idx]})

def rating_gauge(avg_rating: float) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=avg_rating,
        title={"text": "Avg Rating"},
        gauge={"axis": {"range": [1,5]},
               "bar": {"thickness": 0.4}}))
    return fig

# --- NEW: Robust path resolver so it works with your current layout ---
def resolve_data_path() -> Path:
    here = Path(__file__).parent
    candidates = [
        here / "data" / "all_reviews.csv",   # repo-style
        here / "all_reviews.csv",            # your current layout
        Path.cwd() / "data" / "all_reviews.csv",
        Path.cwd() / "all_reviews.csv",
    ]
    for p in candidates:
        if p.exists():
            return p
    st.error(
        "Could not find **all_reviews.csv**. "
        "Place it either next to `app.py` or in a `data/` folder."
    )
    st.stop()

DATA_PATH = resolve_data_path()
df = load_data(str(DATA_PATH))
sent = compute_sentiment(df["review_text"])
df = pd.concat([df, sent], axis=1)

st.title("Customer Review Summarizer")
st.caption("Shows NLP + dashboard skills with sentiment, top terms, and product drill-down.")

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    category = st.selectbox("Category", options=["All"] + sorted(df["category"].unique().tolist()))
    platform = st.selectbox("Platform", options=["All"] + sorted(df["platform"].unique().tolist()))
    product = st.selectbox("Product", options=["All"] + sorted(df["product_name"].unique().tolist()))
    date_min, date_max = st.date_input("Date range", value=[df["review_date"].min().date(), df["review_date"].max().date()])
    st.markdown("---")
    show_verified = st.selectbox("Verified purchase", options=["All", "Yes", "No"])
    n_terms = st.slider("Top terms to show", min_value=6, max_value=30, value=12, step=2)

# Apply filters
mask = (df["review_date"].dt.date >= date_min) & (df["review_date"].dt.date <= date_max)
if category != "All":
    mask &= (df["category"] == category)
if platform != "All":
    mask &= (df["platform"] == platform)
if product != "All":
    mask &= (df["product_name"] == product)
if show_verified != "All":
    mask &= (df["verified_purchase"] == show_verified)

fdf = df[mask].copy()

# Top KPIs
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Reviews", len(fdf))
with col2:
    st.metric("Avg Rating", f"{fdf['rating'].mean():.2f}")
with col3:
    pos = (fdf["label"] == "Positive").mean()
    st.metric("% Positive", f"{100*pos:.1f}%")
with col4:
    st.metric("Products", fdf["product_id"].nunique())

# Charts
c1, c2 = st.columns([2, 1])
with c1:
    by_prod = fdf.groupby("product_name").agg(
        reviews=("review_id", "count"),
        avg_rating=("rating", "mean"),
        pos_share=("label", lambda s: (s=="Positive").mean())
    ).reset_index().sort_values(["pos_share", "avg_rating", "reviews"], ascending=[False, False, False])
    if len(by_prod):
        fig = px.bar(by_prod, x="product_name", y="reviews", hover_data=["avg_rating","pos_share"], title="Reviews by Product")
        fig.update_layout(xaxis_title="", yaxis_title="Reviews", height=360)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data for current filter.")

with c2:
    st.plotly_chart(rating_gauge(fdf["rating"].mean() if len(fdf) else 0), use_container_width=True)

# Sentiment over time
t1 = fdf.groupby(fdf["review_date"].dt.to_period("M")).agg(
    avg_rating=("rating","mean"),
    n_reviews=("review_id","count"),
    pos_share=("label", lambda s: (s=="Positive").mean())
).reset_index()
if len(t1):
    t1["review_date"] = t1["review_date"].astype(str)
    fig2 = px.line(t1, x="review_date", y="avg_rating", markers=True, title="Average Rating Over Time")
    fig2.update_layout(xaxis_title="", yaxis_title="Avg Rating", height=360)
    st.plotly_chart(fig2, use_container_width=True)

# Top terms
st.subheader("Key Terms in Reviews (TF-IDF)")
tt = top_terms(fdf, n_terms=n_terms) if len(fdf) else pd.DataFrame({"term":[],"score":[]})
if len(tt):
    fig3 = px.bar(tt, x="term", y="score", title="Top Terms", height=360)
    fig3.update_layout(xaxis_tickangle=-35)
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("No terms to display with current filter.")

# Table
st.subheader("Reviews")
st.dataframe(
    fdf[["review_date","product_name","platform","verified_purchase","rating","label","review_text"]]
    .sort_values("review_date", ascending=False),
    use_container_width=True
)

# Export filtered data
st.download_button("Download filtered CSV", data=fdf.to_csv(index=False),
                   file_name="filtered_reviews.csv", mime="text/csv")

st.markdown("---")
st.caption("Sentiment by VADER; key terms by TF-IDF (1–2 grams). CSV can be next to app.py or under data/.")
