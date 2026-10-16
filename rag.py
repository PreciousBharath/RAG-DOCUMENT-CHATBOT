"""Minimal, dependency-light Retrieval-Augmented Generation engine.

Pipeline: load -> chunk (with overlap) -> index (TF-IDF vectors) -> retrieve top-k
-> build grounded prompt -> generate with any OpenAI-compatible LLM
(OpenAI, Groq, Together, Ollama, LM Studio...). Without an API key it falls
back to an extractive answer so the demo always works offline.
"""
import io
import os
import re
from dataclasses import dataclass

import numpy as np
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


_STOP = TfidfVectorizer(stop_words="english").get_stop_words()


def analyzer(text: str):
    """Lowercase, drop stop-words, light stemming (passwords -> password) + bigrams."""
    toks = []
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if w in _STOP:
            continue
        for suf in ("ing", "es", "s"):
            if len(w) > 4 and w.endswith(suf):
                w = w[: -len(suf)]
                break
        toks.append(w)
    return toks + [a + " " + b for a, b in zip(toks, toks[1:])]


def split_sentences(text: str):
    return re.split(r"(?<=[.!?])(?<!Rs\.)(?<!No\.)\s+", text)


@dataclass
class Chunk:
    text: str
    source: str
    idx: int


def load_file(name: str, data: bytes) -> str:
    if name.lower().endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(io.BytesIO(data)).pages)
    return data.decode("utf-8", errors="ignore")


def chunk_text(text: str, source: str, size: int = 90, overlap: int = 25):
    """Word-window chunking with overlap so answers spanning boundaries are not lost."""
    words = re.sub(r"\s+", " ", text).split()
    chunks, step = [], max(1, size - overlap)
    for i, start in enumerate(range(0, max(1, len(words) - overlap), step)):
        piece = " ".join(words[start:start + size])
        if piece:
            chunks.append(Chunk(piece, source, i))
    return chunks


class VectorStore:
    def __init__(self, chunks):
        self.chunks = chunks
        self.vec = TfidfVectorizer(analyzer=analyzer, sublinear_tf=True)
        self.matrix = self.vec.fit_transform([c.text for c in chunks])

    def search(self, query: str, k: int = 4):
        sims = cosine_similarity(self.vec.transform([query]), self.matrix).ravel()
        top = np.argsort(sims)[::-1][:k]
        return [(self.chunks[i], float(sims[i])) for i in top if sims[i] > 0]


SYSTEM_PROMPT = (
    "You are a precise assistant. Answer ONLY from the provided context. "
    "Cite sources as [1], [2]. If the answer is not in the context, say you don't know."
)


def build_prompt(question, hits):
    ctx = "\n\n".join(f"[{i+1}] ({c.source}) {c.text}" for i, (c, _) in enumerate(hits))
    return f"Context:\n{ctx}\n\nQuestion: {question}\nAnswer with citations:"


def generate(question, hits, api_key=None, base_url=None, model=None, temperature=0.2):
    if not hits:
        return "I couldn't find anything relevant in the uploaded documents.", "none"
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if api_key:
        url = (base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1").rstrip("/") + "/chat/completions"
        r = requests.post(url, timeout=60, headers={"Authorization": f"Bearer {api_key}"}, json={
            "model": model or "gpt-4o-mini", "temperature": temperature,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                         {"role": "user", "content": build_prompt(question, hits)}],
        })
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"], "llm"
    return extractive_answer(question, hits), "extractive"


def extractive_answer(question, hits, n=3):
    """Offline fallback: pick the sentences most similar to the question."""
    sents = []
    for i, (c, _) in enumerate(hits):
        for s in split_sentences(c.text):
            if len(s.split()) > 3:
                sents.append((s.strip(), i + 1))
    if not sents:
        return hits[0][0].text
    v = TfidfVectorizer(analyzer=analyzer).fit([s for s, _ in sents] + [question])
    sims = cosine_similarity(v.transform([question]), v.transform([s for s, _ in sents])).ravel()
    if sims.max() == 0:
        return "I couldn't find a direct answer; see the retrieved sources for related passages."
    order = [i for i in np.argsort(sims)[::-1][:n] if sims[i] >= 0.65 * sims.max()]
    best = sorted(order)
    seen, out = set(), []
    for b in best:
        s, ref = sents[b]
        if not any(s in t or t in s for t in seen):
            seen.add(s)
            out.append(f"{s} [{ref}]")
    return " ".join(out)
