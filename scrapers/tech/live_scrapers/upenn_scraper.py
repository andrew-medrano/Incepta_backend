from typing import List, Dict
from bs4 import BeautifulSoup
from scrapers.tech.base_scraper import BaseScraper
import time
from selenium import webdriver

class UPennScraper(BaseScraper):
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
            base_url='https://upenn.technologypublisher.com/?Test_Inteum_Tech_Publisher_PCI%5Bpage%5D=',
            fieldnames=fieldnames,
            headers={
                'User-Agent': 'UPennScraper/1.0',
            }
        )
        self.request_delay = 0.2
        self.driver = None

    def __enter__(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--disable-gpu')
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
        time.sleep(self.request_delay)
        url = f'{self.base_url}{page_number+1}'
        self.driver.get(url)
        time.sleep(0.1)  # Wait for page to load
        return BeautifulSoup(self.driver.page_source, 'html.parser')

    def get_items_from_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract items from a page"""
        items = []
        titles = soup.find_all('a', class_="_name_link_1twmm_25")
        
        for title in titles:
            item = {
                'university': 'University of Pennsylvania',
                'title': title.get_text(strip=True),
                'patent': '',  # UPenn doesn't provide patent numbers on listing page
                'link': title['href'],
            }
            items.append(item)
        
        return items

    def get_item_details(self, link: str) -> Dict[str, str]:
        """Get detailed information for a single item"""
        time.sleep(self.request_delay)
        self.driver.get(link)
        time.sleep(0.1)  # Wait for page to load
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        
        details = {}
        
        # Get the docket number
        number_elem = soup.find('p', class_='technology-side-title', string=lambda text: text and 'Docket:' in text)
        if number_elem:
            details['number'] = number_elem.get_text(strip=True).replace('Docket:', '').strip()
        else:
            details['number'] = ''

        # Get the description
        description_elem = soup.find('div', class_='technology-main')
        if description_elem:
            details['description'] = description_elem.get_text(strip=True)
        else:
            details['description'] = 'No description available'
        
        return details

    def process_item(self, item: Dict[str, str]) -> Dict[str, str]:
        """Process item before adding to dataset"""
        # Ensure all required fields are present
        for field in self.fieldnames:
            if field not in item:
                item[field] = ''
        return item

if __name__ == '__main__':
    with UPennScraper() as scraper:
        try:
            results = scraper.scrape(
                limit=21,  # Number of pages found in notebook
                output_file='data/tech/upenn_2024_12_07.csv'
            )
            print(f"Successfully scraped {len(results)} items")
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
