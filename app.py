import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import uuid
from ollama import Client
from sentence_transformers import SentenceTransformer
import faiss
import pickle

# MongoDB setup
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["drdo_agent_db"]
session_collection = db["chat_sessions"]

# Ollama + Embedding setup
client = Client(host='http://localhost:11434')
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
index = faiss.read_index("vector2.index")
with open("metadata2.pkl", "rb") as f:
    metadata = pickle.load(f)

# Context retrieval
def retrieve_context(query, k=5):
    vec = embedding_model.encode([query])
    distances, indices = index.search(vec, k)
    return [metadata[i] for i in indices[0]]

# Prompt builder
def build_prompt(query, context):
    if not context:
        return None
    context_text = "\n\n".join(
        f"Title: {doc.get('title', 'N/A')}\nURL: {doc.get('url', '')}\n\n{doc.get('content', '')[:1000]}"
        for doc in context
    )
    return f"""You are a factual assistant for DRDO (Defence Research and Development Organisation).

Use ONLY the context below to answer the user's question. Do not use general knowledge.

If the answer is not found in the context, reply:
"No information available from DRDO sources. Visit https://www.drdo.gov.in for more."

Context:
{context_text}

Question: {query}

Answer:"""

# Store chat
def store_chat_message(session_id, role, content):
    session_collection.update_one(
        {"session_id": session_id},
        {
            "$push": {
                "messages": {
                    "role": role,
                    "content": content,
                    "timestamp": datetime.utcnow()
                }
            },
            "$setOnInsert": {
                "session_id": session_id,
                "created_at": datetime.utcnow()
            }
        },
        upsert=True
    )

# Generate answer
def chat_with_mistral(query, session_id):
    store_chat_message(session_id, "user", query)
    context_docs = retrieve_context(query)
    prompt = build_prompt(query, context_docs)

    if not prompt:
        answer = "No information available from DRDO sources. Visit https://www.drdo.gov.in for more."
        store_chat_message(session_id, "assistant", answer)
        return answer

    response = client.chat(
        model="mistral",
        messages=[{"role": "user", "content": prompt}]
    )

    raw_answer = response['message']['content'].strip()
    if "No information available" in raw_answer:
        answer = raw_answer
    else:
        sources = "\n\nSources:\n" + "\n".join(doc.get("url", "") for doc in context_docs if doc.get("url"))
        answer = f"{raw_answer}{sources}"

    store_chat_message(session_id, "assistant", answer)
    return answer

# ----------------- Streamlit UI ------------------ #
st.set_page_config(page_title="DRDO Assistant", layout="wide")
st.title("🛡️ DRDO Assistant")

# Load all sessions
all_sessions = list(session_collection.find({}, {"session_id": 1, "created_at": 1}).sort("created_at", -1))
session_names = [s["session_id"] for s in all_sessions]

# Sidebar
st.sidebar.subheader("💬 Chat Sessions")
new_chat_clicked = st.sidebar.button("➕ New Chat")
selected_session = st.sidebar.radio("Choose a session:", session_names, label_visibility="collapsed") if session_names else None

# Handle new chat
if new_chat_clicked:
    new_session_id = str(uuid.uuid4())
    st.session_state.session_id = new_session_id
    store_chat_message(new_session_id, "assistant", "👋 You can ask questions about DRDO.")
    st.rerun()

# Handle session switching
if selected_session and selected_session != st.session_state.get("session_id"):
    st.session_state.session_id = selected_session
    st.rerun()

# If no session selected, show nothing
if "session_id" not in st.session_state:
    st.info("Start a new chat to begin.")
    st.stop()

# Display chat history
messages = session_collection.find_one({"session_id": st.session_state.session_id}) or {}
for msg in messages.get("messages", []):
    st.chat_message(msg["role"]).markdown(msg["content"])

# Input
user_input = st.chat_input("Ask your DRDO-related question here...")
if user_input:
    st.chat_message("user").markdown(user_input)
    with st.chat_message("assistant"):
        with st.spinner("🔎 Processing your question..."):
            answer = chat_with_mistral(user_input, st.session_state.session_id)
            st.markdown(answer)
