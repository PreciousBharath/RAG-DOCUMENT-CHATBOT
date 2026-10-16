"""DocuMind - Chat with your documents (Retrieval-Augmented Generation).
Run:  streamlit run app.py
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from rag import VectorStore, chunk_text, generate, load_file
from sample_docs import SAMPLE_DOCS, SAMPLE_QUESTIONS

st.set_page_config(page_title="DocuMind RAG", page_icon="🧠", layout="wide")

with st.sidebar:
    st.header("📚 Knowledge base")
    files = st.file_uploader("Upload PDF / TXT / MD", type=["pdf", "txt", "md"], accept_multiple_files=True)
    use_samples = st.checkbox("Include sample company documents", value=True)
    st.header("⚙️ Retrieval")
    chunk_size = st.slider("Chunk size (words)", 40, 300, 90, 10)
    top_k = st.slider("Top-k chunks", 1, 8, 4)
    st.header("🤖 LLM (optional)")
    api_key = st.text_input("OpenAI-compatible API key", type="password", help="Leave empty for offline extractive mode")
    base_url = st.text_input("Base URL", "https://api.openai.com/v1", help="Works with Groq, Together, Ollama (http://localhost:11434/v1)...")
    model = st.text_input("Model", "gpt-4o-mini")

docs = {f.name: load_file(f.name, f.read()) for f in files} if files else {}
if use_samples:
    docs.update(SAMPLE_DOCS)


@st.cache_resource(show_spinner="Indexing documents…")
def build_index(items: tuple, size: int):
    chunks = [c for name, text in items for c in chunk_text(text, name, size=size, overlap=size // 4)]
    return VectorStore(chunks)


st.markdown("<h1 style='margin-bottom:0'>🧠 DocuMind — Chat with your Documents</h1>"
            "<p style='color:#888'>Retrieval-Augmented Generation: grounded answers with source citations, no hallucinated facts</p>",
            unsafe_allow_html=True)
if not docs:
    st.info("Upload a document or enable the sample knowledge base.")
    st.stop()

store = build_index(tuple(sorted(docs.items())), chunk_size)
m = st.columns(4)
m[0].metric("Documents", len(docs))
m[1].metric("Chunks indexed", len(store.chunks))
m[2].metric("Vocabulary", f"{len(store.vec.vocabulary_):,}")
m[3].metric("Mode", "LLM" if api_key else "Offline")

st.session_state.setdefault("history", [])
st.write("**Try:**")
cols = st.columns(len(SAMPLE_QUESTIONS))
clicked = None
for c, q in zip(cols, SAMPLE_QUESTIONS):
    if c.button(q, width="stretch"):
        clicked = q

chat_col, src_col = st.columns([3, 2])
question = st.chat_input("Ask a question about your documents…") or clicked
if question:
    hits = store.search(question, top_k)
    try:
        answer, mode = generate(question, hits, api_key or None, base_url, model)
    except Exception as e:  # network / auth problems -> graceful fallback
        answer, mode = generate(question, hits)
        answer = f"⚠️ LLM call failed ({e.__class__.__name__}); showing extractive answer.\n\n" + answer
    st.session_state.history.append({"q": question, "a": answer, "hits": hits, "mode": mode})

with chat_col:
    for turn in st.session_state.history[-4:]:
        st.chat_message("user").write(turn["q"])
        st.chat_message("assistant", avatar="🧠").write(turn["a"])
    if not st.session_state.history:
        st.chat_message("assistant", avatar="🧠").write("Hi! Ask me anything about the loaded documents.")

with src_col:
    st.subheader("📎 Retrieved sources")
    if st.session_state.history:
        hits = st.session_state.history[-1]["hits"]
        df = pd.DataFrame([{"ref": f"[{i+1}]", "source": c.source, "score": s} for i, (c, s) in enumerate(hits)])
        fig = px.bar(df, x="score", y="ref", orientation="h", color="source", text_auto=".2f",
                     color_discrete_sequence=["#8E2DE2", "#00C9FF", "#FF416C"], title="Relevance (cosine similarity)")
        fig.update_layout(height=230, margin=dict(t=40, b=10), yaxis=dict(autorange="reversed"), legend=dict(orientation="h", y=-0.3))
        st.plotly_chart(fig, width="stretch")
        for i, (c, s) in enumerate(hits):
            with st.expander(f"[{i+1}] {c.source} · chunk {c.idx} · score {s:.2f}", expanded=i == 0):
                st.write(c.text)
    else:
        st.caption("Sources used for the latest answer appear here.")
