import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import random
import json
import re
import fitz  # PyMuPDF
import tempfile
import os

class JSONScraperWithPDF:
    def __init__(self, base_url, output_file="scraped_data.json"):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls = set()
        self.queue = [base_url]
        self.data = []
        self.output_file = output_file

    def is_valid_url(self, url):
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.netloc == self.domain

    def extract_main_content(self, soup):
        for tag in soup(['script', 'style', 'meta', 'head', 'footer', 'header', 'noscript']):
            tag.extract()

        main_area = soup.find('main') or soup.find('article') or soup.body
        if not main_area:
            return "", ""

        raw_text = main_area.get_text(separator='\n', strip=True)
        cleaned_text = ' '.join(raw_text.split())
        return raw_text, cleaned_text

    def extract_text_from_pdf(self, pdf_url):
        try:
            response = requests.get(pdf_url, timeout=15)
            if response.status_code != 200:
                return None, None

            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                tmp_pdf.write(response.content)
                tmp_pdf_path = tmp_pdf.name

            text_content = ""
            with fitz.open(tmp_pdf_path) as doc:
                for page in doc:
                    text_content += page.get_text()

            os.remove(tmp_pdf_path)
            cleaned = ' '.join(text_content.split())
            return text_content.strip(), cleaned

        except Exception as e:
            print(f"✗ PDF error: {pdf_url} ({e})")
            return None, None

    def crawl(self, delay=2, max_pages=None):
        count = 0
        while self.queue and (max_pages is None or count < max_pages):
            url = self.queue.pop(0)
            if url in self.visited_urls:
                continue

            try:
                time.sleep(delay + random.uniform(0.5, 1.0))
                headers = {
                    'User-Agent': 'Mozilla/5.0',
                    'Accept': 'text/html',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                response = requests.get(url, headers=headers, timeout=15)

                if response.status_code == 200:
                    self.visited_urls.add(url)
                    count += 1

                    soup = BeautifulSoup(response.text, 'html.parser')
                    title = soup.title.string.strip() if soup.title else "No Title"
                    raw_text, cleaned_text = self.extract_main_content(soup)

                    self.data.append({
                        "url": url,
                        "title": title,
                        "content": raw_text,
                        "cleaned_content": cleaned_text
                    })

                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        full_url = urljoin(url, href)

                        if full_url.endswith('.pdf') and full_url not in self.visited_urls:
                            self.visited_urls.add(full_url)
                            print(f"  ↳ PDF Found: {full_url}")
                            pdf_text, pdf_clean = self.extract_text_from_pdf(full_url)
                            if pdf_text:
                                self.data.append({
                                    "url": full_url,
                                    "title": os.path.basename(full_url),
                                    "content": pdf_text,
                                    "cleaned_content": pdf_clean
                                })

                        elif self.is_valid_url(full_url) and full_url not in self.visited_urls and full_url not in self.queue:
                            self.queue.append(full_url)

                    print(f"✓ Scraped: {url} ({count})")

            except Exception as e:
                print(f"✗ Failed: {url} ({e})")

        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

        print(f"\n✅ Done. {len(self.data)} entries saved to {self.output_file}")

# Usage
if __name__ == "__main__":
    scraper = JSONScraperWithPDF(base_url="https://www.drdo.gov.in", output_file="drdo_scraped_with_pdfs2.json")
    scraper.crawl(delay=2, max_pages=None)
