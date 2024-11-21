from typing import List, Dict
from bs4 import BeautifulSoup
from Incepta_backend.scrapers.tech.base_scraper import BaseScraper

class TemplateScraper(BaseScraper):
    def __init__(self):
        # Define the fields your scraper will collect
        fieldnames = [
            'title',
            'link',
            'description',
            'develop'
        ]
        
        super().__init__(
            base_url='https://example.com',  # Replace with your target website
            fieldnames=fieldnames,
            headers={
                'User-Agent': 'YourScraperName/1.0 (your@email.com)',
                # Add any other headers needed...
            }
        )

    def get_page_soup(self, page_number: int) -> BeautifulSoup:
        """Fetch and parse a single page"""
        url = f'{self.base_url}/page/{page_number}'  # Modify URL pattern as needed
        response = self.session.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')

    def get_items_from_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract items from a page"""
        items = []
        # Find all items on the page
        elements = soup.find_all('div', class_='item')  # Modify selector as needed
        
        for element in elements:
            item = {
                'title': element.find('h2').text.strip(),  # Modify selectors as needed
                'link': self.make_absolute_url(element.find('a')['href']),
                # Add other fields...
            }
            items.append(item)
        
        return items

    def get_item_details(self, link: str) -> Dict[str, str]:
        """Get detailed information for a single item"""
        response = self.session.get(link)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        details = {
            # Add detailed information extraction
            # 'price': soup.find('span', class_='price').text.strip(),
            # 'description': soup.find('div', class_='description').text.strip(),
        }
        
        return details

    def process_item(self, item: Dict[str, str]) -> Dict[str, str]:
        """Optional: Process item before adding to dataset"""
        # Add any cleaning or processing logic here
        return item


if __name__ == '__main__':
    # Example usage
    with TemplateScraper() as scraper:
        try:
            # Scrape 5 pages and save to output.csv
            results = scraper.scrape(
                limit=5,
                output_file='output.csv'
            )
            print(f"Successfully scraped {len(results)} items")
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
