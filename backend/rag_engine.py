import os
import re
from openai import OpenAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv

load_dotenv()

FAISS_PATH  = os.path.join(os.path.dirname(__file__), "..", "faiss_store")
TOP_K       = 4
MAX_HISTORY = 6
MODEL       = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are a helpful assistant for Markgrid.ai — an AI Visibility Platform.

RULES:
1. Answer ONLY using the context below. Do not use outside knowledge.
2. If context doesn't have the answer, say: "I don't have enough information about that. Visit markgrid.ai for details."
3. Never invent features, pricing, or claims not in the context.
4. Include relevant URLs from the context naturally in your answer.
5. Be concise and direct.
6. You will receive a CONVERSATION HISTORY before the current question. Use that history to understand references like "the 3rd point", "tell me more about that", "explain the first one" etc. Always resolve what the user is referring to using previous messages before answering.
7. If the user refers to something from a previous answer (like "3rd point" or "that feature"), look at the conversation history to find what they mean, then answer about that specific thing.

CONTEXT (Markgrid.ai content):
{context}

CONVERSATION HISTORY + CURRENT QUESTION will follow below.
"""

GREETING_RE = re.compile(
    r"^(hi|hello|hey|thanks|thank you|bye|who are you|what can you do|help)[\s!?.]*$",
    re.IGNORECASE,
)


class RAGEngine:
    def __init__(self):
        print("⏳  Loading embedding model ...")
        self.embedder = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        print("⏳  Loading FAISS index ...")
        self.vectorstore = FAISS.load_local(
            FAISS_PATH,
            self.embedder,
            allow_dangerous_deserialization=True,
        )
        print("✅  FAISS loaded")
        self.llm = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
        )
        print("✅  Groq ready")

    def chat(self, user_message, history):
        if GREETING_RE.match(user_message.strip()):
            return {
                "answer": "Hey! I'm the Markgrid assistant. Ask me anything about the platform — features, pricing, solutions, and more.",
                "sources": [],
                "low_confidence": False,
            }

        results = self.vectorstore.similarity_search_with_score(user_message, k=TOP_K)

        print(f"\n🔍 Query: {user_message}")
        for doc, score in results:
            print(f"  Score: {score:.4f} | URL: {doc.metadata.get('url')} | Preview: {doc.page_content[:80]}")

        if not results or results[0][1] > 1.5:
            return {
                "answer": "I'm not confident I have accurate information about that. Please visit markgrid.ai or email hello@markgrid.ai.",
                "sources": [],
                "low_confidence": True,
            }

        context_parts = []
        seen_urls = []
        for doc, score in results:
            url   = doc.metadata.get("url", "")
            title = doc.metadata.get("title", "")
            context_parts.append(f"[Source: {title} | {url}]\n{doc.page_content}")
            if url and url not in seen_urls:
                seen_urls.append(url)

        context = "\n\n---\n\n".join(context_parts)

    # Build full message array with history
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(context=context)}
        ]

    # Add every previous turn so LLM remembers the full conversation
        for turn in history:
            messages.append({"role": turn["role"], "content": turn["content"]})

    # Add current user message
        messages.append({"role": "user", "content": user_message})

        print(f"\n📜 Sending {len(messages)} messages to LLM (including {len(history)} history turns)")

        response = self.llm.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=600,
            temperature=0.2,
        )

        return {
            "answer": response.choices[0].message.content.strip(),
            "sources": seen_urls,
            "low_confidence": False,
        }