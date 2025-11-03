import os, sys, json
import pandas as pd
import numpy as np

try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY","")) if os.getenv("OPENAI_API_KEY") else None
except Exception:
    client = None

def summarize_dataframe(df):
    desc = df.describe(include="all").to_dict()
    anomalies = {}
    for col in df.select_dtypes(include=[np.number]).columns:
        z = (df[col] - df[col].mean())/ (df[col].std() + 1e-9)
        idx = np.where(np.abs(z) > 3)[0].tolist()
        if idx:
            anomalies[col] = idx
    return {"shape": df.shape, "columns": df.columns.tolist(), "describe": desc, "anomalies": anomalies}

def ai_narrative(summary):
    if client:
        try:
            msg = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role":"user","content": f"Write a concise business insight report (bullets) from this Excel data summary: {json.dumps(summary)[:6000]}"}],
                temperature=0.2
            )
            return msg.choices[0].message.content
        except Exception as e:
            return f"(OpenAI error) {e}"
    return "Set OPENAI_API_KEY to enable AI narrative."

def main(path):
    xls = pd.ExcelFile(path)
    lines = ["# Excel AI Assistant Report", ""]
    for sheet in xls.sheet_names:
        df = xls.parse(sheet)
        summary = summarize_dataframe(df)
        lines.append(f"## {sheet}")
        lines.append(f"- Rows: {df.shape[0]}, Cols: {df.shape[1]}")
        lines.append(f"- Anomalous columns: {list(summary['anomalies'].keys())}")
        lines.append("### AI Narrative")
        lines.append(ai_narrative(summary))
        lines.append("")
    out = os.path.splitext(path)[0] + "_ai_report.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {out}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python main.py your.xlsx")
        sys.exit(1)
    main(sys.argv[1])
