# 🛡️ DRDO AI Customer Support Agent
A private, searchable chatbot built using scraped data from the [DRDO](https://www.drdo.gov.in) website. It answers queries strictly based on official content — no hallucinations, no general answers. Perfect for research, public transparency, and information seekers. A local, intelligent chatbot assistant powered by **Ollama**, **FAISS**, and **MongoDB**, built to answer user queries **strictly using DRDO (Defence Research and Development Organisation) content**. Supports chat history and document-aware answers.  

Built with **Streamlit**, this app offers a ChatGPT-like interface for exploring DRDO's public content.

---

## 🚀 Features

- 💬 Conversational DRDO Q&A assistant
- 🔍 Uses vector search (FAISS + MiniLM) to retrieve relevant DRDO data
- 🧠 Powered by open-source LLMs using **Ollama** (e.g., `mistral`)
- 🗂️ Stores full chat history in **MongoDB** (per session)
- 📄 Parses HTML pages and PDFs from DRDO website
- 🔗 Returns document links as sources with every response
- 🖥️ Beautiful UI via Streamlit with sidebar history (like ChatGPT)
---

## 📦 Project Structure

| File | Purpose |
|------|---------|
| `app.py` | Streamlit frontend UI |
| `session_chat.py` | Handles session-based chat management |
| `mongo_integration.py` | Logic for chatbot response + MongoDB logging |
| `scrapeContent.py`, `crawl.py`, `clean.py` | Scraper for extracting structured data from DRDO website |
| `convert_json.py` | Converts scraped content to `newoutput.json` |
| `vectorizeddata.ipynb` | Vectorizes cleaned data using `SentenceTransformer` |
| `vector2.index`, `metadata2.pkl` | FAISS index and metadata for fast semantic retrieval |
| `drdo_scraped_with_pdfs2.json`, `newoutput.json` | Cleaned and structured data |
| `requirements.txt` | All necessary dependencies |
| `connecting_mondoDb.py` | MongoDB connection test script |
| `web3.py` | Miscellaneous logic module |
| `drdo_output.rar` | Archived backup of old JSON outputs |

---


## 📦 Tech Stack

| Component        | Tech Used                                  |
|------------------|---------------------------------------------|
| Language Model   | [Ollama](https://ollama.com) + Mistral      |
| Embeddings       | `sentence-transformers/all-MiniLM-L6-v2`    |
| Vector DB        | FAISS                                       |
| Database         | MongoDB (local or Atlas)                    |
| UI               | Streamlit                                   |
| PDF Parsing      | PyMuPDF / pdfminer                          |
| Web Scraping     | `requests`, `BeautifulSoup`                 |

---

## 🛠 Setup Instructions (Windows)

### 1. Clone the repository

```bash
git clone https://github.com/Shine-5705/Customer_Support_Agent.git
cd Customer_Support_Agent
```

### 2. Install Dependencies
Install Python packages:
```bash
pip install -r requirements.txt
```

### 3. Start MongoDB
Make sure MongoDB is installed and running:
```bash
mongod
```
(Optional: Use MongoDB Compass to view chat logs)

### 4. Start Ollama + Mistral
Download and install Ollama: https://ollama.com
Then pull Mistral model:
```bash
ollama pull mistral
```
### 5. Scrape DRDO Website (Optional)
If not already done, run:

```bash
python scraper.py
```
This will generate drdo_scraped_with_pdfs.json which is used for vector search.

### 6. Build Vector Index
```bash
python vectorizeddata.py
```
This will generate vector.index and metadata.pkl.


### 7. Launch Streamlit App
```bash
streamlit run app.py
```

## 🧑‍💻 How It Works

1. `scrapeContent.py` and `crawl.py` gather content from DRDO site
2. `convert_json.py` cleans and converts it into structured format
3. `vectorizeddata.ipynb` uses SentenceTransformer to embed text
4. FAISS (`vector2.index`) stores vector data for fast search
5. `mongo_integration.py` loads this data and connects to Ollama (Mistral)
6. `session_chat.py` and `app.py` power the frontend interface

## 🧠 Chat Logic

- Uses only DRDO content
- Adds source links automatically
- Stores all questions and answers in MongoDB (`chat_sessions` collection)


## 🧪 Example Sources

```
https://www.drdo.gov.in/drdo/who-is-who
https://www.drdo.gov.in/drdo/labs-establishment
```

## 📌 Deployment

For public access (free option):
- 🖥️ Host locally via Streamlit Share (experimental) or Cloudflare Tunnels
- 💾 Deploy MongoDB using MongoDB Atlas (free tier)
- 🧠 Ollama must run locally due to Mistral LLM

*Hugging Face Spaces not supported because Ollama and FAISS need GPU/local inference.*


## 📄 License
MIT License

## 🙏 Acknowledgements
- [Ollama](https://ollama.com)
- [DRDO Official Website](https://www.drdo.gov.in)
- [HuggingFace Sentence Transformers](https://huggingface.co/sentence-transformers)
- [Streamlit](https://streamlit.io)
