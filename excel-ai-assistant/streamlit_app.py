
import os, json
import pandas as pd
import numpy as np
import streamlit as st

# Optional OpenAI client for AI narrative
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY","")) if os.getenv("OPENAI_API_KEY") else None
except Exception:
    client = None

st.set_page_config(page_title="Excel AI Assistant", layout="wide")

def summarize_dataframe(df: pd.DataFrame):
    desc = df.describe(include="all").replace({np.nan: None}).to_dict()
    anomalies = {}
    for col in df.select_dtypes(include=[np.number]).columns:
        std = df[col].std()
        if std is None or np.isnan(std) or std == 0:
            continue
        z = (df[col] - df[col].mean()) / (std + 1e-9)
        idx = np.where(np.abs(z) > 3)[0].tolist()
        if idx:
            anomalies[col] = idx
    return {"shape": df.shape, "columns": df.columns.tolist(), "describe": desc, "anomalies": anomalies}

def ai_narrative(summary: dict):
    # Return AI-generated bullet insights if API key is configured; otherwise a helpful message.
    if client:
        try:
            msg = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user",
                           "content": f"Write a concise business insight report (bullets) from this Excel data summary: {json.dumps(summary)[:6000]}"}],
                temperature=0.2
            )
            return msg.choices[0].message.content
        except Exception as e:
            return f"(OpenAI error) {e}"
    return "Set the OPENAI_API_KEY environment variable to enable the AI narrative."

st.title("📊 Excel AI Assistant")
st.caption("Upload an Excel file (.xlsx). I’ll summarize each sheet, flag anomalies, and (optionally) generate AI insights.")

with st.sidebar:
    st.header("Upload")
    uploaded = st.file_uploader("Excel file (.xlsx)", type=["xlsx"])
    st.markdown("---")
    st.subheader("Tips")
    st.write("- For AI insights, set `OPENAI_API_KEY` before running.")
    st.write("- Download a sample file from the project or use the default bundled path.")

# Load workbook
if uploaded is not None:
    xls = pd.ExcelFile(uploaded)
    source_name = uploaded.name
else:
    st.info("No file uploaded — trying to use local 'sample_excel_ai.xlsx'.")
    try:
        xls = pd.ExcelFile("sample_excel_ai.xlsx")
        source_name = "sample_excel_ai.xlsx"
    except Exception as e:
        st.error("No file uploaded and 'sample_excel_ai.xlsx' not found. Please upload a file.")
        st.stop()

st.write(f"**Workbook:** {source_name}")
st.write(f"**Sheets found:** {', '.join(xls.sheet_names)}")

def render_sheet(sheet_name: str):
    st.subheader(f"📄 {sheet_name}")
    df = xls.parse(sheet_name)
    st.dataframe(df.head(20), use_container_width=True)
    summary = summarize_dataframe(df)

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Rows", summary["shape"][0])
    with c2:
        st.metric("Columns", summary["shape"][1])
    with c3:
        st.metric("Numeric cols w/ anomalies", len(summary["anomalies"]))

    with st.expander("Descriptive statistics (raw)"):
        st.json(summary["describe"])

    if summary["anomalies"]:
        st.markdown("**Anomalies (|z| > 3):**")
        for col, idxs in summary["anomalies"].items():
            st.write(f"- `{col}`: {len(idxs)} rows → indices {idxs[:15]}{' ...' if len(idxs) > 15 else ''}")
    else:
        st.success("No z-score anomalies detected in numeric columns.")

    st.markdown("### AI Narrative")
    narrative = ai_narrative(summary)
    st.write(narrative)

    st.markdown("---")
    return sheet_name, summary, narrative

all_summaries = []
for sheet in xls.sheet_names:
    all_summaries.append(render_sheet(sheet))

# Download consolidated Markdown report
if st.button("Generate Markdown Report"):
    lines = ["# Excel AI Assistant Report", ""]
    for sheet, summary, narrative in all_summaries:
        lines.append(f"## {sheet}")
        lines.append(f"- Rows: {summary['shape'][0]}, Cols: {summary['shape'][1]}")
        lines.append(f"- Anomalous columns: {list(summary['anomalies'].keys())}")
        lines.append("### AI Narrative")
        lines.append(narrative if isinstance(narrative, str) else str(narrative))
        lines.append("")
    md = "\n".join(lines)
    st.download_button("Download report.md", data=md.encode("utf-8"), file_name="excel_ai_report.md", mime="text/markdown")

st.markdown("---")
st.markdown("**How to run locally:**")
st.code("""
pip install streamlit pandas numpy openai
export OPENAI_API_KEY="sk-proj-..."   # (macOS/Linux) or $env:OPENAI_API_KEY="sk-proj-..." on Windows
streamlit run streamlit_app.py
""", language="bash")
