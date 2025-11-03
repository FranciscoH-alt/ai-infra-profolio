# app.py
import os
import io
import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
import faiss

# Optional OpenAI (only used if OPENAI_API_KEY is present)
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", ""))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
except Exception:
    client = None
    has_openai = False

st.set_page_config(page_title="FAQ Chatbot (RAG)", layout="wide")
st.title("FAQ Chatbot")

# -------- Helpers --------
def chunk_text(text: str, max_chars: int = 900, overlap: int = 120):
    """
    Simple character-based chunking with overlap.
    Keeps chunks a reasonable size for embeddings and LLM context.
    """
    text = text.strip().replace("\r", "")
    if not text:
        return []

    chunks = []
    start = 0
    n = len(text)
    while start < n:
        end = min(start + max_chars, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == n:
            break
        start = end - overlap
        if start < 0:
            start = 0
    return chunks

@st.cache_resource(show_spinner=False)
def load_embed_model():
    # Cache the model only once per session
    return SentenceTransformer("all-MiniLM-L6-v2")

embed_model = load_embed_model()

@st.cache_data(show_spinner=False)
def build_index(files):
    """
    Reads 1–5 PDFs, extracts text, chunks it, embeds, and builds FAISS index.
    Returns (index, chunks) where chunks[i] matches the vector at index i.
    """
    all_chunks = []

    for f in files:
        # Streamlit returns UploadedFile objects; PdfReader accepts bytes buffer
        b = io.BytesIO(f.read())
        reader = PdfReader(b)

        for page in reader.pages:
            raw = page.extract_text() or ""
            # First split on blank lines, then re-chunk to consistent size
            rough_parts = [p for p in raw.split("\n\n") if p.strip()]
            for part in rough_parts:
                all_chunks.extend(chunk_text(part, max_chars=900, overlap=120))

    if not all_chunks:
        return None, []

    vecs = embed_model.encode(all_chunks, convert_to_numpy=True, normalize_embeddings=True)
    vecs = vecs.astype("float32")

    index = faiss.IndexFlatIP(vecs.shape[1])  # cosine with normalized vectors
    index.add(vecs)
    return index, all_chunks

def retrieve(index, chunks, query, k=5):
    qv = embed_model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype("float32")
    D, I = index.search(qv, k)
    ctxs = [chunks[i] for i in I[0]]
    sims = [float(d) for d in D[0]]
    return list(zip(ctxs, sims))

def call_openai(context, question):
    """Calls OpenAI only if OPENAI_API_KEY is set."""
    if not has_openai or client is None:
        return None, "No OPENAI_API_KEY found. Showing retrieved context instead."

    prompt = (
        "Answer concisely using ONLY the provided context. "
        "If the answer is not in the context, say you don't see it.\n\n"
        f"CONTEXT:\n{context}\n\nQ: {question}"
    )
    try:
        # Chat Completions API
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return resp.choices[0].message.content, None
    except Exception as e:
        return None, f"OpenAI error: {e}"

# -------- UI --------
uploaded = st.file_uploader("Upload 1–5 PDFs", type=["pdf"], accept_multiple_files=True)
query = st.text_input("Ask a question:")

with st.sidebar:
    st.subheader("Notes")
    st.write("- Uses **SentenceTransformers** (all-MiniLM-L6-v2) for embeddings.")
    st.write("- FAISS **inner product** with normalized vectors ≈ cosine similarity.")
    st.write("- Set `OPENAI_API_KEY` to get LLM answers; otherwise you'll see the top matches.")
    if st.button("Clear caches"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("Cleared cached data and models. Reload the page.")

if uploaded:
    index, chunks = build_index(uploaded)
    if chunks:
        st.success(f"Indexed {len(chunks)} chunks.")
    else:
        st.warning("No extractable text found in the PDFs.")

    if query and chunks:
        top = retrieve(index, chunks, query, k=5)
        context = "\n\n---\n\n".join([c for c, _ in top])

        col1, col2 = st.columns([2, 1])
        with col1:
            if has_openai:
                answer, err = call_openai(context, query)
                if answer:
                    st.markdown("### Answer")
                    st.markdown(answer)
                else:
                    st.warning(err or "Model call failed.")
                    st.code(context)
            else:
                st.info("Set `OPENAI_API_KEY` to enable model answers. Showing retrieved context instead:")
                st.code(context)

        with col2:
            st.markdown("### 🔎 Top Matches")
            for i, (c, sim) in enumerate(top, start=1):
                with st.expander(f"Match #{i} • similarity={sim:.3f}", expanded=(i == 1)):
                    st.write(c)

else:
    st.info("Upload PDFs to start.")
