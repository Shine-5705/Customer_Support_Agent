from ollama import Client
from sentence_transformers import SentenceTransformer
import faiss
import pickle
from pymongo import MongoClient
from datetime import datetime

# ✅ Connect to MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["drdo_agent_db"]
chat_collection = db["chat_logs"]

# ✅ Load FAISS vector index and metadata
index = faiss.read_index("vector2.index")
with open("metadata2.pkl", "rb") as f:
    metadata = pickle.load(f)

# ✅ Load embedding model and Ollama client
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
client = Client(host='http://localhost:11434')

# ✅ Retrieve relevant context documents
def retrieve_context(query, k=5):
    vec = embedding_model.encode([query])
    distances, indices = index.search(vec, k)
    return [metadata[i] for i in indices[0]]

# ✅ Build DRDO-safe prompt
def build_prompt(query, context):
    if not context:
        return None
    context_text = "\n\n".join(
        f"Title: {doc.get('title', 'N/A')}\nURL: {doc.get('url', '')}\n\n{doc.get('cleaned_content', '')[:1000]}"
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

# ✅ Save each message to MongoDB
def store_message(role, content):
    chat_collection.insert_one({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow()
    })

# ✅ Chat logic with Mistral model
def chat_with_mistral(query):
    store_message("user", query)

    context_docs = retrieve_context(query)
    prompt = build_prompt(query, context_docs)

    if not prompt:
        answer = "No information available from DRDO sources. Visit https://www.drdo.gov.in for more."
        store_message("assistant", answer)
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

    store_message("assistant", answer)
    return answer

# ✅ Chat loop
if __name__ == "__main__":
    while True:
        user_query = input("🧠 You: ")
        if user_query.lower() in ["exit", "quit"]:
            break
        reply = chat_with_mistral(user_query)
        print("\n🤖 Agent:", reply)
