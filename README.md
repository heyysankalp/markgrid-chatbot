# Markgrid AI Chatbot

A RAG-based intelligent chatbot built for Markgrid.ai as part of a technical evaluation.

## Live Demo
[Coming soon — link after deployment]

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite + Tailwind CSS |
| Backend | FastAPI (Python) |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 (local) |
| Vector Store | FAISS (cosine similarity) |
| LLM | LLaMA 3.3 70B via Groq API |
| Text Splitting | LangChain RecursiveCharacterTextSplitter |

## Architecture
User Query

↓

Greeting Check (regex) → direct reply if hi/hello/thanks

↓

Embed query with MiniLM (384-dim vector)

↓

FAISS cosine similarity search → top 4 chunks

↓

Confidence threshold check (reject irrelevant queries)

↓

Build prompt: System + Context + Conversation History + Query

↓

LLaMA 3.3 70B via Groq API

↓

Return answer + source URLs to React frontend

## Key Decisions

- **RAG over fine-tuning**: Cheaper, faster to update, more accurate for factual queries
- **MiniLM over OpenAI embeddings**: Free, runs locally, no API dependency
- **FAISS over ChromaDB**: Works on Python 3.14+, faster, no external dependencies
- **Chunk size 500 / overlap 100**: 20% overlap preserves context at chunk boundaries
- **Temperature 0.2**: Reduces hallucination while keeping answers natural
- **Confidence threshold**: Irrelevant questions never reach the LLM

## Guardrails

1. Cosine similarity threshold — rejects off-topic queries before LLM call
2. System prompt — LLM instructed to only use provided context
3. Low temperature (0.2) — reduces hallucination

## Local Setup

### Prerequisites
- Python 3.11
- Node.js 18+
- Groq API key (free at console.groq.com)

### Backend
```bash
cd backend
pip install -r requirements.txt
echo "GROQ_API_KEY=your_key_here" > .env
python3 ingest.py        # run once to build vector store
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173
