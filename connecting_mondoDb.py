from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")  # localhost and default port
db = client["drdo_agent_db"]                        # create or connect to database
collection = db["chat_logs"]                        # create or connect to collection

# Insert sample document
collection.insert_one({"role": "user", "content": "Hello, this is a test!", "timestamp": "2025-05-13T12:00:00Z"})

# Retrieve all entries
for doc in collection.find():
    print(doc)
