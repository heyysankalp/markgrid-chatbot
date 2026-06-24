# Markgrid AI Chatbot

A RAG-based intelligent chatbot built for Markgrid.ai as part of a technical evaluation. The bot accurately answers user queries about Markgrid's platform, features, pricing, and brand identity using content scraped directly from markgrid.ai.

---

## Live Demo

🔗 [Coming soon after deployment]

---

## GitHub Repository

🔗 https://github.com/heyysankalp/markgrid-chatbot

---

## Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Frontend | React + Vite + Tailwind CSS | Fast, modern, industry standard |
| Backend | FastAPI (Python) | Async, type-safe, production-ready |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | Free, local, no API dependency |
| Vector Store | FAISS | Fast, lightweight, no external dependencies |
| Text Splitting | LangChain RecursiveCharacterTextSplitter | Context-aware, natural boundary splitting |
| LLM | LLaMA 3.3 70B via Groq API | Free tier, fast inference (<1s) |
| Data Source | Scraped markgrid.ai JSON | Direct source, always accurate |

---

## Architecture

```
User sends a message
        ↓
Greeting check (regex) → direct reply if hi/hello/thanks
        ↓
Embed query using MiniLM (384-dimensional vector)
        ↓
FAISS cosine similarity search → retrieve top 4 chunks
        ↓
Confidence threshold check → reject irrelevant queries
        ↓
Build prompt: System Instructions + Context Chunks + Conversation History + Query
        ↓
Send to LLaMA 3.3 70B via Groq API (temperature=0.2)
        ↓
Return answer + source URLs to React frontend
```

---

## Implementation Details

### 1. Data Collection
Markgrid.ai was scraped into a structured JSON file containing 20 pages. Each entry has three fields: `url`, `title`, and `text`. The URL is stored as metadata and surfaced to the user whenever relevant.

### 2. Text Preprocessing
Before chunking, boilerplate text that appears across every page (e.g. "Talk to Sales", "Ready to Transform Your AI Visibility?") is stripped out. This prevents noise from polluting the embeddings and degrading retrieval quality.

### 3. Chunking Strategy
Used LangChain's `RecursiveCharacterTextSplitter` with:
- **Chunk size:** 500 characters
- **Chunk overlap:** 100 characters (20%)
- **Separators:** `\n\n` → `\n` → `. ` → ` ` → `""`

The recursive approach tries to split at paragraph breaks first, then line breaks, then sentence endings — always at the most natural boundary available. The 20% overlap ensures that content spanning a chunk boundary is present in both adjacent chunks, so no information is lost at the edges.

### 4. Embeddings
Each chunk is embedded using `sentence-transformers/all-MiniLM-L6-v2`, a lightweight model that:
- Runs entirely on CPU (no GPU required)
- Produces 384-dimensional vectors
- Captures semantic meaning, not just keywords

All vectors are L2-normalized (`normalize_embeddings=True`), which is required for cosine similarity to work correctly with FAISS.

### 5. Vector Store (FAISS)
Facebook AI Similarity Search (FAISS) stores all chunk embeddings on disk. At query time, the user's question is embedded with the same MiniLM model and compared against all stored vectors using cosine similarity. The top 4 most relevant chunks are retrieved in milliseconds.

FAISS was chosen over ChromaDB because it supports Python 3.14+, has no external service dependencies, and is significantly faster for this data size.

### 6. Retrieval & Confidence Threshold
After retrieval, the cosine distance score of the best matching chunk is checked against a threshold. If the score is too high (meaning the query is too far from any stored content), the bot returns a polite deflection without calling the LLM. This prevents hallucination on off-topic queries.

### 7. LLM Prompting
The prompt sent to LLaMA 3.3 70B contains four parts:
1. **System instructions** — role definition, rules, anti-hallucination constraints
2. **Retrieved context** — top 4 chunks with their source URLs and titles
3. **Conversation history** — last 6 turns for multi-turn coherence
4. **Current user query**

Temperature is set to 0.2 to reduce creative generation and keep answers grounded in the provided context.

### 8. Guardrails (Anti-Hallucination)
Three layers of protection:
1. **Similarity threshold** — irrelevant queries never reach the LLM
2. **System prompt** — LLM explicitly instructed to only use provided context
3. **Low temperature (0.2)** — reduces creativity, keeps answers factual

### 9. Conversation History
Message history is maintained on the frontend as an array and sent with every API request. The backend prepends the last 6 turns to the LLM prompt, giving the model context of the ongoing conversation. The backend is fully stateless — no session storage required.

### 10. Source URL Attribution
Every chunk carries the URL of its source page as metadata. After retrieval, unique URLs from all returned chunks are collected and returned to the frontend, where they appear as clickable source chips below each bot response.

---

## Guardrails Summary

| Guardrail | How it works |
|---|---|
| Off-topic rejection | Cosine similarity threshold — query must be close enough to stored content |
| No hallucination | LLM instructed to only answer from provided context |
| Low creativity | Temperature 0.2 keeps answers grounded |
| Greeting handling | Regex detects greetings and bypasses retrieval entirely |
| Uncertainty disclosure | Bot explicitly says when it doesn't have enough information |

---

## Local Setup

### Prerequisites
- Python 3.11
- Node.js 18+
- Groq API key — free at console.groq.com

### Backend Setup
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Add your Groq API key
echo "GROQ_API_KEY=your_key_here" > .env

# Build vector store (run once)
python3 ingest.py

# Start the API server
uvicorn main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Open http://localhost:5173

---

## Key Design Decisions

**RAG over fine-tuning** — Fine-tuning is expensive, slow, and requires retraining every time Markgrid updates their website. RAG is real-time, cheap to update, and more accurate for specific factual queries because it retrieves the exact source text.

**Local embeddings over OpenAI embeddings** — MiniLM runs on CPU with no API cost or dependency. For a prototype with ~200 chunks, it performs comparably to paid embedding APIs.

**FAISS over managed vector DBs** — Pinecone and ChromaDB add infrastructure complexity. FAISS runs in-process, persists to two files on disk, and handles this data size with zero overhead.

**Groq over OpenAI** — Groq's free tier provides LLaMA 3.3 70B with sub-second inference speeds, making it ideal for a real-time chat interface without cost concerns.

---

## Project Structure

```
markgrid-chatbot/
├── backend/
│   ├── main.py          # FastAPI server, CORS, endpoints
│   ├── rag_engine.py    # Core RAG logic, retrieval, LLM call
│   ├── ingest.py        # One-time ingestion pipeline
│   ├── requirements.txt
│   └── .env             # GROQ_API_KEY (not committed)
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── hooks/
│   │   │   └── useChat.js        # State management, API calls
│   │   └── components/
│   │       ├── ChatWindow.jsx    # Main UI, input bar
│   │       ├── Message.jsx       # Chat bubbles
│   │       ├── TypingIndicator.jsx
│   │       ├── SourceChips.jsx   # Clickable source URLs
│   │       └── SuggestedQuestions.jsx
│   └── index.html
├── data/
│   └── markgrid_data.json   # Scraped Markgrid content
└── faiss_store/             # Generated by ingest.py
    ├── index.faiss
    └── index.pkl
```
