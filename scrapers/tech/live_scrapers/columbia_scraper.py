from typing import List, Dict
from bs4 import BeautifulSoup
from scrapers.tech.base_scraper import BaseScraper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import logging

class ColumbiaScraper(BaseScraper):
    def __init__(self):
        fieldnames = [
            'university',
            'title',
            'number',
            'patent',
            'link',
            'description'
        ]
        
        super().__init__(
            base_url='https://inventions.techventures.columbia.edu/categories',
            fieldnames=fieldnames,
            headers={
                'User-Agent': 'ColumbiaScraper/1.0',
            }
        )
        self.request_delay = 0.2
        self.driver = None

    def __enter__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')  # Use new headless mode
        options.add_argument('--disable-gpu')  # Required for some systems
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(options=options)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.quit()
        return super().__exit__(exc_type, exc_val, exc_tb)

    def get_page_soup(self, page_number: int) -> BeautifulSoup:
        """Fetch and parse a single page"""
        url = self.base_url
        if page_number > 0:
            url = f"{self.base_url}?p={page_number + 1}"
            
        self.driver.get(url)
        time.sleep(0.1)  # Wait for initial load
        
        # Scroll down to load all content
        body = self.driver.find_element(By.TAG_NAME, "body")
        prev_count = 0
        
        for i in range(10):  # Reduced from 50 since we're paginating
            # Scroll down
            for _ in range(3):
                body.send_keys(Keys.PAGE_DOWN)
            time.sleep(0.1)  # Wait for content to load
            
            current_cards = self.driver.find_elements(By.CSS_SELECTOR, ".Result_resultCard__iJcI0")
            current_count = len(current_cards)
            
            if current_count == prev_count:
                break
                
            prev_count = current_count
        
        return BeautifulSoup(self.driver.page_source, 'html.parser')

    def get_items_from_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract items from a page"""
        items = []
        cards = soup.find_all('div', class_="Result_resultCard__iJcI0")
        
        for card in cards:
            title_elem = card.select_one(".Result_resultTitle__Lt8Y6 a span")
            link_elem = card.select_one(".Result_resultTitle__Lt8Y6 a")
            id_elem = card.select_one(".md-up")
            
            if title_elem and link_elem:
                # Make sure we have a full URL
                link = link_elem['href']
                if not link.startswith('http'):
                    link = f"https://inventions.techventures.columbia.edu{link}"
                    
                item = {
                    'university': 'Columbia',
                    'title': title_elem.text.strip(),
                    'number': id_elem.text.strip() if id_elem else '',
                    'patent': '',
                    'link': link,
                }
                items.append(item)
        
        return items

    def get_item_details(self, link: str) -> Dict[str, str]:
        """Get detailed information for a single item"""
        time.sleep(self.request_delay)
        logging.info(f"Fetching details from: {link}")
        self.driver.get(link)
        time.sleep(0.1)
        
        try:
            description_elem = self.driver.find_element(
                By.CSS_SELECTOR, 
                ".Typography_body1__SeQ9n.DetailsWithData_detailsBody__wcTdA"
            )
            return {'description': description_elem.text.strip()}
        except Exception as e:
            logging.warning(f"Could not find description for {link}: {str(e)}")
            return {'description': 'No description available'}

    def process_item(self, item: Dict[str, str]) -> Dict[str, str]:
        """Process item before adding to dataset"""
        if not item.get('description'):
            item['description'] = 'No description available'
        return item

if __name__ == '__main__':
    with ColumbiaScraper() as scraper:
        try:
            results = scraper.scrape(
                limit=158,  # Only need one "page" since it's infinite scroll
                output_file='data/tech/columbia_2024_11_26.csv'
            )
            print(f"Successfully scraped {len(results)} items")
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")