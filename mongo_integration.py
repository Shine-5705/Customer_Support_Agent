from ollama import Client
from sentence_transformers import SentenceTransformer
import faiss
import pickle
from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB
mongo_client = MongoClient("mongodb://localhost:27017/")
db = mongo_client["chat_db"]
chat_collection = db["conversations"]

# Load FAISS vector index and metadata
index = faiss.read_index("vector2.index")
with open("metadata2.pkl", "rb") as f:
    metadata = pickle.load(f)

embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
client = Client(host='http://localhost:11434')

def retrieve_context(query, k=5):
    vec = embedding_model.encode([query])
    distances, indices = index.search(vec, k)
    return [metadata[i] for i in indices[0]]

def build_prompt(query, context):
    context_text = "\n\n".join(
        f"Title: {doc.get('title', 'N/A')}\nURL: {doc.get('url', '')}\n\n{doc.get('content', '')[:1000]}"
        for doc in context
    )
    return f"""You are a helpful assistant. Use the context below to answer the question.

Context:
{context_text}

Question: {query}

Answer:"""

def store_message(role, content):
    chat_collection.insert_one({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow()
    })

def chat_with_mistral(query):
    store_message("user", query)
    context_docs = retrieve_context(query)
    prompt = build_prompt(query, context_docs)

    response = client.chat(
        model="mistral",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response['message']['content']
    store_message("assistant", answer)
    return answer

# Run chatbot loop
if __name__ == "__main__":
    while True:
        user_query = input("🧠 You: ")
        if user_query.lower() in ["exit", "quit"]:
            break
        reply = chat_with_mistral(user_query)
        print("\n🤖 Agent:", reply)
