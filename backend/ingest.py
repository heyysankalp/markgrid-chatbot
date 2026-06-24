import json
import re
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
DATA_PATH  = os.path.join(os.path.dirname(__file__), "..", "data", "markgrid_data.json")
FAISS_PATH = os.path.join(os.path.dirname(__file__), "..", "faiss_store")

CHUNK_SIZE    = 500
CHUNK_OVERLAP = 100


def clean_text(text):
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    for phrase in [
        "Talk to Sales",
        "Priority onboarding • Launch pricing locked • Cancel anytime",
        "Ready to Transform Your AI Visibility?",
        "Start a conversation with the Markgrid team.",
        "We will walk you through how the platform fits your specific marketing function.",
    ]:
        text = text.replace(phrase, "")
    return text.strip()


def load_documents():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        pages = json.load(f)
    docs = []
    for page in pages:
        url   = page.get("url", "")
        title = page.get("title", "")
        text  = page.get("text", "")
        if not text.strip():
            continue
        docs.append({"text": clean_text(text), "metadata": {"url": url, "title": title}})
    print(f"✅  Loaded {len(docs)} pages")
    return docs


def split_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    chunks = []
    for doc in docs:
        for i, part in enumerate(splitter.split_text(doc["text"])):
            chunks.append(Document(
                page_content=part.strip(),
                metadata={**doc["metadata"], "chunk_index": i},
            ))
    print(f"✅  Split into {len(chunks)} chunks")
    return chunks


def embed_and_store(chunks):
    print("⏳  Loading embedding model ...")
    embedder = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
    print(f"⏳  Embedding {len(chunks)} chunks ...")
    vectorstore = FAISS.from_documents(chunks, embedder)
    os.makedirs(FAISS_PATH, exist_ok=True)
    vectorstore.save_local(FAISS_PATH)
    print(f"🎉  Done! FAISS index saved to {FAISS_PATH}")


if __name__ == "__main__":
    print("\n=== Markgrid RAG Ingestion ===\n")
    embed_and_store(split_documents(load_documents()))