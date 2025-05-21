import os
import re

def load_and_clean_texts(directory):
    all_docs = []
    for file in os.listdir(directory):
        if file.endswith(".txt") and not file.startswith("pdf_links"):
            with open(os.path.join(directory, file), encoding="utf-8") as f:
                text = f.read()
                # Basic cleanup
                cleaned = re.sub(r"\s+", " ", text)
                all_docs.append(cleaned)
    return all_docs
