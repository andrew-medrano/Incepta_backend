from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Type
import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
from tenacity import retry, stop_after_attempt, wait_fixed

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')

class BaseScraper(ABC):
    """Base class for web scrapers"""
    
    def __init__(self, base_url: str, fieldnames: List[str], headers: Dict[str, str] = None):
        self.base_url = base_url
        self.fieldnames = fieldnames
        default_headers = {
            'User-Agent': 'YourScraperName/1.0 (contact@example.com)'
        }
        self.headers = headers or default_headers
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def clean_text(text):
        """Clean text by removing inconsistent quotes and standardizing format"""
        if not isinstance(text, str):
            return text
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace('"', '""')
        text = text.replace('\n', '\\n').replace('\r', '')
        text = text.replace('\x00', '')
        return text

    @abstractmethod
    def get_page_soup(self, page_number: int) -> BeautifulSoup:
        """Fetch and parse a single page"""
        pass

    @abstractmethod
    def get_items_from_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract items from a page"""
        pass

    @abstractmethod
    def get_item_details(self, link: str) -> Dict[str, str]:
        """Get detailed information for a single item"""
        pass

    def process_item(self, item: Dict[str, str]) -> Dict[str, str]:
        """Process item before adding to dataset (can be overridden by subclasses)"""
        return item

    def scrape(self, limit: int = None, output_file: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Main scraping method to collect and save data
        """
        all_items = []
        logging.info("Starting scraping process...")
        
        current_page = 1
        while limit is None or current_page <= limit:
            logging.info(f"Processing page {current_page}...")
            
            # Get page content
            try:
                page_soup = self.get_page_soup(current_page)
                items = self.get_items_from_page(page_soup)
                
                if not items:
                    logging.info("No more items found. Stopping pagination.")
                    break
                
                logging.info(f"Found {len(items)} items on page {current_page}")
                
                # Get details for each item
                for i, item in enumerate(items, 1):
                    logging.info(f"Fetching details for item {i}/{len(items)} on page {current_page}")
                    details = self.get_item_details(item['link'])
                    item.update(details)
                    processed_item = self.process_item(item)
                    all_items.append(processed_item)
                
                current_page += 1
                
            except Exception as e:
                logging.error(f"Error processing page {current_page}: {str(e)}")
                break

        if output_file:
            logging.info(f"Saving {len(all_items)} items to {output_file}")
            df = pd.DataFrame(all_items, columns=self.fieldnames)
            df.to_csv(output_file, index=False)
            logging.info("Save complete!")

        logging.info(f"Scraping complete! Total items collected: {len(all_items)}")
        return all_items

    def make_absolute_url(self, url: str) -> str:
        """Convert a relative URL to an absolute URL"""
        from urllib.parse import urljoin
        return urljoin(self.base_url, url)

    def __enter__(self) -> 'BaseScraper':
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb) -> None:
        self.session.close()
