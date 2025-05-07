import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import time
import random
import re
from pdfminer.high_level import extract_text

class WebsiteScraper:
    def __init__(self, base_url, output_folder="scraped_data"):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls = set()
        self.queue = [base_url]
        self.output_folder = output_folder
        self.text_folder = os.path.join(output_folder, "text_content")
        self.html_folder = os.path.join(output_folder, "html_content")
        self.pdf_folder = os.path.join(output_folder, "pdfs")

        os.makedirs(self.text_folder, exist_ok=True)
        os.makedirs(self.html_folder, exist_ok=True)
        os.makedirs(self.pdf_folder, exist_ok=True)

        print(f"Text content folder: {os.path.abspath(self.text_folder)}")
        print(f"HTML content folder: {os.path.abspath(self.html_folder)}")
        print(f"PDF folder: {os.path.abspath(self.pdf_folder)}")

    def is_valid_url(self, url):
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.netloc == self.domain

    def extract_text_content(self, soup):
        for tag in soup(["script", "style", "noscript", "meta", "head"]):
            tag.extract()

        title = soup.title.string.strip() if soup.title else "No Title"
        content_areas = soup.find_all(['article', 'main', 'div', 'section'],
                                      class_=re.compile(r'content|main|article|text|body'))
        if not content_areas:
            content_areas = [soup.body] if soup.body else []

        text_blocks = [f"TITLE: {title}\n\n"]
        for area in content_areas:
            for element in area.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']):
                text = element.get_text(strip=True)
                if text and len(text) > 5:
                    if element.name.startswith('h'):
                        text_blocks.append(f"\n{element.name.upper()}: {text}\n")
                    else:
                        text_blocks.append(text)
        return "\n\n".join(text_blocks)

    def create_filename(self, url, extension='.html'):
        parsed_url = urlparse(url)
        path = parsed_url.path.strip('/') or 'index'
        filename = path.replace('/', '_').replace('\\', '_')
        if parsed_url.query:
            query_part = parsed_url.query.replace('&', '_').replace('=', '-')[:50]
            base, ext = os.path.splitext(filename)
            filename = f"{base}_{query_part}"
        filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
        if not filename.endswith(extension):
            filename = os.path.splitext(filename)[0] + extension
        if len(filename) > 150:
            import hashlib
            filename = hashlib.md5(url.encode()).hexdigest() + extension
        return filename

    def save_content(self, url, html_content, text_content):
        html_filename = self.create_filename(url, '.html')
        text_filename = self.create_filename(url, '.txt')

        html_path = os.path.join(self.html_folder, html_filename)
        text_path = os.path.join(self.text_folder, text_filename)

        try:
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✓ Saved HTML: {url} as {html_path}")
        except Exception as e:
            print(f"✗ Failed to save HTML for {url}: {e}")
            return False

        try:
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            print(f"✓ Saved Text: {url} as {text_path}")
            return True
        except Exception as e:
            print(f"✗ Failed to save text for {url}: {e}")
            return False

    def download_and_parse_pdf(self, url):
        try:
            response = requests.get(url, stream=True, timeout=15)
            if response.status_code == 200:
                filename = self.create_filename(url, extension=".pdf")
                pdf_path = os.path.join(self.pdf_folder, filename)

                with open(pdf_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                print(f"✓ Downloaded PDF: {url}")

                try:
                    text = extract_text(pdf_path)
                    text_filename = self.create_filename(url, extension=".txt")
                    text_path = os.path.join(self.text_folder, text_filename)
                    with open(text_path, 'w', encoding='utf-8') as f:
                        f.write(text)
                    print(f"✓ Extracted text from PDF: {text_path}")
                except Exception as e:
                    print(f"✗ Failed to extract text from PDF {url}: {e}")
            else:
                print(f"✗ Failed to download PDF {url}: status code {response.status_code}")
        except Exception as e:
            print(f"✗ Error downloading PDF {url}: {e}")

    def crawl(self, delay=2, max_pages=None):
        count = 0
        print(f"Starting crawl of {self.base_url}")
        print(f"Files will be saved to: {os.path.abspath(self.output_folder)}")

        while self.queue and (max_pages is None or count < max_pages):
            url = self.queue.pop(0)
            if url in self.visited_urls:
                continue

            print(f"\nProcessing: {url}")
            try:
                time.sleep(delay + random.uniform(0.5, 1.0))
                headers = {
                    'User-Agent': 'Mozilla/5.0',
                    'Accept': 'text/html,application/xhtml+xml,application/xml',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                response = requests.get(url, headers=headers, timeout=15)

                if response.status_code == 200:
                    self.visited_urls.add(url)
                    count += 1
                    soup = BeautifulSoup(response.text, 'html.parser')
                    text_content = self.extract_text_content(soup)
                    saved = self.save_content(url, response.text, text_content)

                    if saved:
                        links_found = 0
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            full_url = urljoin(url, href)

                            if full_url.lower().endswith('.pdf'):
                                if full_url not in self.visited_urls:
                                    self.visited_urls.add(full_url)
                                    self.download_and_parse_pdf(full_url)
                                continue

                            if (self.is_valid_url(full_url) and 
                                full_url not in self.visited_urls and 
                                full_url not in self.queue):
                                self.queue.append(full_url)
                                links_found += 1

                        print(f"  Found {links_found} new links")
                print(f"Progress: {count} pages processed. Queue size: {len(self.queue)}")
            except requests.exceptions.RequestException as e:
                print(f"  Network error for {url}: {e}")
            except Exception as e:
                print(f"  Error processing {url}: {e}")

        print(f"\nCrawling completed. Visited {len(self.visited_urls)} pages.")

# Usage
if __name__ == "__main__":
    scraper = WebsiteScraper(base_url="https://www.drdo.gov.in", output_folder="drdo_data")
    scraper.crawl(delay=2, max_pages=50)
