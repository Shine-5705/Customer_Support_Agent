import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import time
import random
import re

class WebsiteScraper:
    def __init__(self, base_url, output_folder="scraped_data"):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.visited_urls = set()
        self.queue = [base_url]
        self.output_folder = output_folder
        self.text_folder = os.path.join(output_folder, "text_content")
        self.html_folder = os.path.join(output_folder, "html_content")
        
        # Create output folders if they don't exist
        os.makedirs(self.text_folder, exist_ok=True)
        os.makedirs(self.html_folder, exist_ok=True)
        print(f"Text content folder: {os.path.abspath(self.text_folder)}")
        print(f"HTML content folder: {os.path.abspath(self.html_folder)}")
    
    def is_valid_url(self, url):
        """Check if URL is valid and belongs to the same domain"""
        parsed = urlparse(url)
        return bool(parsed.netloc) and parsed.netloc == self.domain
    
    def extract_text_content(self, soup):
        """Extract meaningful text content from the page"""
        # Remove script and style elements
        for script_or_style in soup(["script", "style", "noscript", "meta", "head"]):
            script_or_style.extract()
        
        # Get the page title
        title = soup.title.string.strip() if soup.title else "No Title"
        
        # Extract text from specific content areas if they exist
        content_areas = soup.find_all(['article', 'main', 'div', 'section'], 
                                    class_=re.compile(r'content|main|article|text|body'))
        
        if not content_areas:
            # If no specific content areas found, use body
            content_areas = [soup.body] if soup.body else []
        
        text_blocks = []
        text_blocks.append(f"TITLE: {title}\n\n")
        
        # Process each content area
        for area in content_areas:
            # Extract all text elements
            for element in area.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']):
                text = element.get_text(strip=True)
                if text and len(text) > 5:  # Skip very short text
                    if element.name.startswith('h'):
                        # Format headings
                        text_blocks.append(f"\n{element.name.upper()}: {text}\n")
                    else:
                        text_blocks.append(text)
        
        # Join all text with proper spacing
        return "\n\n".join(text_blocks)
    
    def create_filename(self, url, extension='.html'):
        """Create a valid filename from the URL"""
        parsed_url = urlparse(url)
        path = parsed_url.path
        
        # Handle the base URL or empty path
        if not path or path == '/':
            filename = 'index' + extension
        else:
            # Create a filename from the path
            path = path.strip('/')
            
            # Replace special characters
            filename = path.replace('/', '_').replace('\\', '_')
            
            # Add extension if it doesn't have the right one
            if not filename.endswith(extension):
                # Remove any existing extension
                filename = os.path.splitext(filename)[0] + extension
        
        # Add query parameters to filename if present
        if parsed_url.query:
            query_part = parsed_url.query.replace('&', '_').replace('=', '-')[:50]  # Limit length
            base, ext = os.path.splitext(filename)
            filename = f"{base}_{query_part}{ext}"
        
        # Ensure the filename is valid
        filename = ''.join(c for c in filename if c.isalnum() or c in '._-')
        
        return filename
    
    def save_content(self, url, html_content, text_content):
        """Save both HTML and text content to files"""
        html_filename = self.create_filename(url, '.html')
        text_filename = self.create_filename(url, '.txt')
        
        # Save HTML content
        html_filepath = os.path.join(self.html_folder, html_filename)
        try:
            with open(html_filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"✓ Saved HTML: {url} as {html_filepath}")
        except Exception as e:
            print(f"✗ Failed to save HTML for {url}: {str(e)}")
            return False
        
        # Save text content
        text_filepath = os.path.join(self.text_folder, text_filename)
        try:
            with open(text_filepath, 'w', encoding='utf-8') as f:
                f.write(text_content)
            print(f"✓ Saved Text: {url} as {text_filepath}")
            return True
        except Exception as e:
            print(f"✗ Failed to save text for {url}: {str(e)}")
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
                    
                    # Extract text content
                    text_content = self.extract_text_content(soup)
                    
                    # Save both HTML and text content
                    saved = self.save_content(url, response.text, text_content)
                    
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
    # Set max_pages to None to crawl the entire website
    scraper.crawl(delay=2, max_pages=50)