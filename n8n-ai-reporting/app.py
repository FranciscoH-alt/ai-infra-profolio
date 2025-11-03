# streamlit run app.py
import streamlit as st
from analytics import daily_kpis, top_products_30d
from gpt_sql import ask

st.title("AI Reporting Infrastructure")
tab1, tab2 = st.tabs(["Hand-written SQL","Ask in English"])

with tab1:
    s, e = st.date_input("Range", value=("2025-10-01","2025-10-29"))
    st.write(daily_kpis(str(s), str(e)))
    st.write(top_products_30d(15))

with tab2:
    q = st.text_input("Ask a question", "Top 10 products by sales in the last 30 days")
    if st.button("Run"):
        df, sql, why = ask(q)
        st.code(sql, language="sql")
        st.caption(why)
        st.dataframe(df)
