from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Type
import aiohttp
from bs4 import BeautifulSoup
import csv
import pandas as pd
from tqdm import tqdm
import logging
import asyncio
from aiohttp import ClientSession
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

    def clean_text(text):
        """Clean text by removing inconsistent quotes and standardizing format"""
        if not isinstance(text, str):
            return text
        # Replace curly/smart quotes with straight quotes
        text = text.replace('"', '"').replace('"', '"')
        # Escape any remaining double quotes
        text = text.replace('"', '""')
        # Replace newlines with \n literal
        text = text.replace('\n', '\\n').replace('\r', '')
        # Remove any null bytes or other problematic characters
        text = text.replace('\x00', '')
        return text

    @abstractmethod
    async def get_page_soup(self, session: ClientSession, page_number: int) -> BeautifulSoup:
        """Fetch and parse a single page"""
        pass

    @abstractmethod
    def get_items_from_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract items from a page"""
        pass

    @abstractmethod
    async def get_item_details(self, session: ClientSession, link: str) -> Dict[str, str]:
        """Get detailed information for a single item"""
        pass

    def process_item(self, item: Dict[str, str]) -> Dict[str, str]:
        """Process item before adding to dataset (can be overridden by subclasses)"""
        return item

    async def scrape(self, limit: int = None, output_file: Optional[str] = None, max_concurrent: int = 10) -> List[Dict[str, str]]:
        """
        Main scraping method to collect and save data
        """
        all_items = []
        logging.info(f"Starting scraping process with max {max_concurrent} concurrent requests...")
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            # First, get all pages concurrently
            page_tasks = []
            current_page = 1
            pagination_stopped = False
            
            for page_num in range(1, limit + 1 if limit else 999999):
                if pagination_stopped:
                    logging.info("Pagination stopped by user. Exiting loop.")
                    break

                logging.info(f"Processing page {page_num}...")
                page_tasks.append(self.get_page_soup(session, page_num))
                
                # Process in batches to avoid overwhelming the server
                if len(page_tasks) >= max_concurrent:
                    logging.info(f"Fetching batch of {len(page_tasks)} pages...")
                    pages = await asyncio.gather(*page_tasks)
                    page_tasks = []
                    
                    # Extract items from pages
                    items = []
                    for page_soup in pages:
                        page_items = self.get_items_from_page(page_soup)
                        if not page_items:
                            logging.info("No more items found. Stopping pagination.")
                            pagination_stopped = True
                            break
                        items.extend(page_items)
                    
                    logging.info(f"Found {len(items)} items in current batch")
                    
                    # Get details for items concurrently
                    detail_tasks = []
                    for item in items:
                        detail_tasks.append(self.get_item_details(session, item['link']))
                    
                    # Process detail tasks in batches
                    for i in range(0, len(detail_tasks), max_concurrent):
                        batch = detail_tasks[i:i + max_concurrent]
                        logging.info(f"Fetching details for items {i+1}-{i+len(batch)}/{len(items)}")
                        details = await asyncio.gather(*batch)
                        
                        # Update items with their details
                        for j, detail in enumerate(details):
                            item = items[i + j]
                            item.update(detail)
                            processed_item = self.process_item(item)
                            all_items.append(processed_item)

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

    async def __aenter__(self) -> 'BaseScraper':
        return self

    async def __aexit__(self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb) -> None:
        pass