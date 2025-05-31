import uuid
from ollama import Client
from sentence_transformers import SentenceTransformer
import faiss, pickle
from pymongo import MongoClient
from datetime import datetime

# MongoDB Setup
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["drdo_agent_db"]
chat_collection = db["chat_logs"]

# Ollama + Embeddings
client = Client(host='http://localhost:11434')
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# FAISS Load
index = faiss.read_index("vector2.index")
with open("metadata2.pkl", "rb") as f:
    metadata = pickle.load(f)

# Context Retrieval
def retrieve_context(query, k=5):
    vec = embedding_model.encode([query])
    distances, indices = index.search(vec, k)
    return [metadata[i] for i in indices[0]]

# Prompt Construction
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

# Chat Storage
def store_chat_message(session_id, role, content):
    chat_collection.update_one(
        {"session_id": session_id},
        {
            "$push": {
                "messages": {
                    "role": role,
                    "content": content,
                    "timestamp": datetime.utcnow()
                }
            }
        },
        upsert=True
    )

# Main Chat Handler
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


if __name__ == "__main__":
    print("📂 Do you want to:")
    print("1. Start a new chat")
    print("2. Continue from existing chat")

    choice = input("Enter 1 or 2: ").strip()

    if choice == "2":
        sessions = list(chat_collection.find({}, {"session_id": 1}))
        print("\n🧾 Existing Sessions:")
        for i, s in enumerate(sessions):
            print(f"{i+1}. Session ID: {s['session_id']}")
        session_choice = int(input("\nEnter session number: ")) - 1
        session_id = sessions[session_choice]['session_id']
    else:
        session_id = str(uuid.uuid4())
        print(f"🆕 New chat started. Session ID: {session_id}")

    while True:
        user_query = input("🧠 You: ")
        if user_query.lower() in ["exit", "quit"]:
            print(f"💾 Chat saved under session ID: {session_id}")
            break
        reply = chat_with_mistral(user_query, session_id)
        print("\n🤖 Agent:", reply)
