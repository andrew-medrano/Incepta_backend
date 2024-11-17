from abc import ABC, abstractmethod
from typing import List, Dict
import requests
from bs4 import BeautifulSoup
import csv
from tqdm import tqdm

class BaseScraper(ABC):
    """Base class for web scrapers"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()

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

    def scrape(self, limit: int, output_file: str) -> None:
        """
        Main scraping method to collect and save data
        
        Args:
            limit (int): Maximum number of pages to scrape
            output_file (str): Path to save the output CSV file
        """
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ["title", "link", "description"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            with tqdm(total=limit, desc="Scraping pages") as pbar:
                for page_num in range(limit):
                    try:
                        # Get page soup
                        soup = self.get_page_soup(page_num)
                        
                        # Get items from page
                        items = self.get_items_from_page(soup)
                        
                        # Get details for each item
                        for item in items:
                            try:
                                details = self.get_item_details(item['link'])
                                item.update(details)
                                writer.writerow(item)
                                csvfile.flush()
                            except Exception as e:
                                print(f"Error processing item {item['link']}: {str(e)}")
                    
                    except Exception as e:
                        print(f"Error scraping page {page_num}: {str(e)}")
                        print("Saving progress and exiting...")
                        break
                    
                    pbar.update(1)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()