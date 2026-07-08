import streamlit as st
import chromadb
from sentence_transformers import SentenceTransformer
import requests
import json
import os
from datetime import datetime

# ================= CONFIG =================
LOCAL_MODEL_PATH = r"C:\Users\arezo\OneDrive\Desktop\website_crawling\models\all-MiniLM-L6-v2"
DB_PATH = "./data/carvertical_database"
LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

# ================= PAGE =================
st.set_page_config(
    page_title="carVertical Chatbot",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 carVertical AI Assistant")

# ================= SESSION =================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "use_llm" not in st.session_state:
    st.session_state.use_llm = True


# ================= CHATBOT =================
class CarVerticalChatbot:
    def __init__(self, db_path):

        self.embedding_model = SentenceTransformer(
            LOCAL_MODEL_PATH if os.path.exists(LOCAL_MODEL_PATH)
            else "all-MiniLM-L6-v2"
        )

        self.is_ready = False
        self.collection = None

        try:
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection = self.client.get_collection("carvertical_content")
            self.is_ready = self.collection.count() > 0
        except:
            self.is_ready = False

    def search(self, query, top_k=5):

        if not self.is_ready:
            return [], [], []

        query_emb = self.embedding_model.encode(query).tolist()

        results = self.collection.query(
            query_embeddings=[query_emb],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )

        chunks, sources, scores = [], [], []

        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                chunks.append(doc)
                sources.append(results["metadatas"][0][i]["source"])
                scores.append(1 - results["distances"][0][i])

        return chunks, sources, scores

    def ask_llm(self, question, chunks):

        context = "\n\n---\n\n".join(chunks[:3])

        # ✅ IMPROVED PROMPT (LONG ANSWERS)
        prompt = f"""
You are an expert AI assistant for carVertical (vehicle history reports platform).

Use ONLY the context below.

CONTEXT:
{context}

QUESTION:
{question}

INSTRUCTIONS:
- Write a detailed and complete answer
- Use 8–12 sentences minimum when possible
- Explain clearly step-by-step
- Add examples if needed
- Do NOT give short answers
- If information is limited, explain what is known clearly

FINAL ANSWER:
"""

        try:
            r = requests.post(
                LM_STUDIO_URL,
                headers={"Content-Type": "application/json"},
                data=json.dumps({
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    # ✅ IMPORTANT FIXES
                    "temperature": 0.6,
                    "max_tokens": 1200
                }),
                timeout=60
            )

            if r.status_code == 200:
                return r.json()["choices"][0]["message"]["content"]

        except:
            pass

        return None

    def answer(self, question, use_llm=True):

        if not self.is_ready:
            return "❌ Database is empty. Run crawler first.", []

        chunks, sources, scores = self.search(question)

        if not chunks:
            return "❌ No relevant data found.", []

        if use_llm:
            ans = self.ask_llm(question, chunks)
            if ans:
                return ans, list(set(sources))

        return chunks[0], list(set(sources))


# ================= LOAD =================
@st.cache_resource
def load_bot():
    return CarVerticalChatbot(DB_PATH)

bot = load_bot()


# ================= SIDEBAR =================
with st.sidebar:
    st.write("## 📊 Status")

    if bot.is_ready:
        st.success("Database Ready")
        st.write("Chunks:", bot.collection.count())
    else:
        st.error("Database Empty")

    st.session_state.use_llm = st.toggle(
        "Use AI (LLM)",
        value=st.session_state.use_llm
    )


# ================= CHAT HISTORY =================
for msg in st.session_state.messages:

    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])

    else:
        with st.chat_message("assistant"):
            st.markdown(msg["content"]["answer"])

            if msg["content"].get("sources"):
                with st.expander("Sources"):
                    for s in msg["content"]["sources"]:
                        st.write(s)


# ================= INPUT =================
question = st.chat_input("Ask about carVertical...")

if question:

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.spinner("Searching and generating answer..."):

        answer, sources = bot.answer(
            question,
            use_llm=st.session_state.use_llm
        )

    st.session_state.messages.append({
        "role": "assistant",
        "content": {
            "answer": answer,
            "sources": sources,
            "timestamp": datetime.now()
        }
    })

    st.rerun()


# ================= FOOTER =================
st.markdown("---")
st.caption("🚗 carVertical AI Chatbot (RAG System) | Powered by LM Studio + ChromaDB")