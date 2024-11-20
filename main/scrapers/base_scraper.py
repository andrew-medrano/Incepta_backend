from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Type
import requests
from bs4 import BeautifulSoup
import csv
import pandas as pd
from tqdm import tqdm
import logging
from tenacity import retry, stop_after_attempt, wait_fixed

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')

class BaseScraper(ABC):
    """Base class for web scrapers"""
    
    def __init__(self, base_url: str, fieldnames: List[str], headers: Dict[str, str] = None):
        self.base_url = base_url
        self.session = requests.Session()
        default_headers = {
            'User-Agent': 'YourScraperName/1.0 (contact@example.com)'
        }
        self.session.headers.update(headers or default_headers)
        self.fieldnames = fieldnames

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
        
        Args:
            limit (Optional[int]): Maximum number of pages to scrape
            output_file (Optional[str]): Path to save the output CSV file
        
        Returns:
            List[Dict[str, str]]: List of scraped items
        """
        all_items = []
        page_num = 1

        with tqdm(desc="Scraping pages") as pbar:
            while True:
                if limit and page_num > limit:
                    break

                try:
                    # Get page soup
                    soup = self.get_page_soup(page_num)
                    
                    # Get items from page
                    items = self.get_items_from_page(soup)
                    
                    if not items:
                        logging.info("No more items found. Ending scrape.")
                        break
                    
                    # Get details for each item
                    for item in items:
                        try:
                            details = self.get_item_details(item['link'])
                            item.update(details)
                            item = self.process_item(item)
                            all_items.append(item)
                        except Exception as e:
                            logging.error(f"Error processing item {item['link']}: {str(e)}")
                
                except Exception as e:
                    logging.error(f"Error scraping page {page_num}: {str(e)}")
                    break
                
                page_num += 1
                pbar.update(1)

        if output_file:
            df = pd.DataFrame(all_items, columns=self.fieldnames)
            df.to_csv(output_file, index=False)

        return all_items

    def make_absolute_url(self, url: str) -> str:
        """Convert a relative URL to an absolute URL"""
        from urllib.parse import urljoin
        return urljoin(self.base_url, url)

    def __enter__(self) -> 'BaseScraper':
        return self

    def __exit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb) -> None:
        self.session.close()

    def close(self) -> None:
        """Close the session explicitly."""
        self.session.close()