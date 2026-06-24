"""
main.py — FastAPI server.
Run: uvicorn main:app --reload --port 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_engine import RAGEngine

app = FastAPI(title="Markgrid RAG Chatbot API")

# Allow React dev server on 5173 (Vite default)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load once at startup — heavy (embedder + chroma connection)
engine = RAGEngine()


# ── Schemas ────────────────────────────────────────────────────────────────────

class Message(BaseModel):
    role: str      # "user" or "assistant"
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[Message] = []

class ChatResponse(BaseModel):
    answer: str
    sources: list[str]
    low_confidence: bool


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "chunks_loaded": engine.collection.count()}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    history = [{"role": m.role, "content": m.content} for m in req.history]
    result  = engine.chat(req.message, history)

    return ChatResponse(
        answer=result["answer"],
        sources=result["sources"],
        low_confidence=result["low_confidence"],
    )
