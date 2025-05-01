import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import time
import random

class WebsiteScraper:
    def __init__(self, base_url, output_folder="scraped_data"):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls = set()
        self.queue = [base_url]
        self.output_folder = output_folder
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        print(f"Output folder: {os.path.abspath(output_folder)}")
    
    def is_valid_url(self, url):
        """Check if URL is valid and belongs to the same domain"""
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.netloc == self.domain
    
    def save_page(self, url, content):
        """Save the page content to a file"""
        # Create a valid filename from the URL
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # Handle the base URL or empty path
        if not path or path == '/':
            filename = 'index.html'
        else:
            # Create a filename from the path
            path = path.strip('/')
            
            # Replace special characters
            filename = path.replace('/', '_').replace('\\', '_')
            
            # Add extension if missing
            if not any(filename.endswith(ext) for ext in ['.html', '.htm', '.php', '.asp', '.aspx']):
                filename += '.html'
        
        # Add query parameters to filename if present
        if parsed_url.query:
            query_part = parsed_url.query.replace('&', '_').replace('=', '-')[:50]  # Limit length
            filename = f"{filename}_{query_part}"
        
        # Ensure the filename is valid
        filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
        
        # Create subdirectories if needed
        if '/' in path:
            subdirs = path.split('/')
            subdir_path = os.path.join(self.output_folder, *subdirs[:-1])
            os.makedirs(subdir_path, exist_ok=True)
            filepath = os.path.join(subdir_path, filename)
        else:
            filepath = os.path.join(self.output_folder, filename)
        
        # Save the content
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Saved: {url} as {filepath}")
            return True
        except Exception as e:
            print(f"✗ Failed to save {url}: {str(e)}")
            return False
    
    def crawl(self, delay=2, max_pages=None):
        """Crawl the website"""
        count = 0
        
        print(f"Starting crawl of {self.base_url}")
        print(f"Files will be saved to: {os.path.abspath(self.output_folder)}")
        
        while self.queue and (max_pages is None or count < max_pages):
            # Get URL from queue
            url = self.queue.pop(0)
            
            # Skip if already visited
            if url in self.visited_urls:
                continue
            
            print(f"\nProcessing: {url}")
            
            try:
                # Add delay to be respectful
                time.sleep(delay + random.uniform(0.5, 1.0))
                
                # Send request with common headers
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                response = requests.get(url, headers=headers, timeout=15)
                
                # Check if successful
                if response.status_code == 200:
                    # Mark as visited
                    self.visited_urls.add(url)
                    count += 1
                    
                    # Parse HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Save the page
                    saved = self.save_page(url, response.text)
                    
                    if saved:
                        # Extract links
                        links_found = 0
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            full_url = urljoin(url, href)
                            
                            # Check if it's a valid URL and not visited yet
                            if (self.is_valid_url(full_url) and 
                                full_url not in self.visited_urls and 
                                full_url not in self.queue):
                                self.queue.append(full_url)
                                links_found += 1
                        
                        print(f"  Found {links_found} new links")
                
                print(f"Progress: {count} pages processed. Queue size: {len(self.queue)}")
            
            except requests.exceptions.RequestException as e:
                print(f"  Network error for {url}: {str(e)}")
            except Exception as e:
                print(f"  Error processing {url}: {str(e)}")
        
        print(f"\nCrawling completed. Visited {len(self.visited_urls)} pages.")

# Usage
if __name__ == "__main__":
    scraper = WebsiteScraper(base_url="https://www.drdo.gov.in", output_folder="drdo_data")
    # Start with a reasonable limit for testing
    scraper.crawl(delay=2, max_pages=50)