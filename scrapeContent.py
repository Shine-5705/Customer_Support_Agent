import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from collections import deque
import time
import os

class DRDOCrawler:
    def __init__(self, base_url, output_dir="drdo_output", delay=1):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited = set()
        self.queue = deque([base_url])
        self.headers = {"User-Agent": "Mozilla/5.0 (compatible; DRDOWebCrawler/1.0)"}
        self.output_dir = output_dir
        self.delay = delay
        self.pdf_links = []

        os.makedirs(output_dir, exist_ok=True)
        self.robot_parser = RobotFileParser()
        self.robot_parser.set_url(urljoin(base_url, "/robots.txt"))
        self.robot_parser.read()

    def is_allowed(self, url):
        return self.robot_parser.can_fetch(self.headers["User-Agent"], url)

    def is_valid(self, url):
        parsed = urlparse(url)
        return (
            parsed.netloc == self.domain
            and parsed.scheme in {"http", "https"}
        )

    def crawl(self):
        while self.queue:
            url = self.queue.popleft()
            if url in self.visited or not self.is_allowed(url):
                continue

            self.visited.add(url)
            print(f"[→] Crawling: {url}")
            try:
                response = requests.get(url, headers=self.headers, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")

                # Save content from <div id="content">
                content_div = soup.find("div", id="content")
                if content_div:
                    text = content_div.get_text(separator="\n", strip=True)
                    self.save_content(url, text)

                # Collect links
                for link in soup.find_all("a", href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    if not self.is_valid(full_url):
                        continue
                    if full_url.lower().endswith('.pdf'):
                        self.pdf_links.append(full_url)
                    elif full_url not in self.visited:
                        self.queue.append(full_url)

                time.sleep(self.delay)  # Polite crawling

            except Exception as e:
                print(f"[x] Failed to crawl {url}: {e}")

        self.save_pdf_links()

    def save_content(self, url, text):
        filename = self.url_to_filename(url)
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"URL: {url}\n\n{text}")
        print(f"[✔] Saved content to {filepath}")

    def save_pdf_links(self):
        pdf_path = os.path.join(self.output_dir, "pdf_links.txt")
        with open(pdf_path, "w", encoding="utf-8") as f:
            for link in sorted(set(self.pdf_links)):
                f.write(link + "\n")
        print(f"[✔] Saved {len(self.pdf_links)} PDF links to {pdf_path}")

    def url_to_filename(self, url):
        parsed = urlparse(url)
        path = parsed.path.strip("/").replace("/", "_")
        if not path:
            path = "home"
        return f"{path}.txt"

# --- CLI Entrypoint ---
if __name__ == "__main__":
    crawler = DRDOCrawler("https://www.drdo.gov.in/drdo")
    crawler.crawl()
