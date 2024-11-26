from typing import List, Dict
from bs4 import BeautifulSoup
from scrapers.tech.base_scraper import BaseScraper
import time

class MITScraper(BaseScraper):
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
            base_url='https://tlo.mit.edu/industry-entrepreneurs/available-technologies',
            fieldnames=fieldnames,
            headers={
                'User-Agent': 'MITScraper/1.0',
            }
        )
        self.request_delay = 0.2

    def get_page_soup(self, page_number: int) -> BeautifulSoup:
        """Fetch and parse a single page"""
        time.sleep(self.request_delay)
        url = f'{self.base_url}?page={page_number}'
        response = self.session.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')

    def get_items_from_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract items from a page"""
        items = []
        titles = soup.find_all('a', class_="arrow-text arrow-text--hide tech-brief-teaser__link")
        
        for title in titles[1:]:  # Skip first item as it's a header
            item = {
                'university': 'MIT',
                'title': title.get_text(strip=True),
                'patent': '',  # MIT doesn't provide patent numbers on listing page
                'link': 'https://tlo.mit.edu' + title['href'],
            }
            items.append(item)
        
        return items

    def get_item_details(self, link: str) -> Dict[str, str]:
        """Get detailed information for a single item"""
        time.sleep(self.request_delay)
        response = self.session.get(link)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        body = soup.find('div', class_="tech-brief-body")
        description_parts = []
        
        # Extract intro if available
        intro_div = soup.find('div', class_="tech-brief-details__intro")
        if intro_div:
            description_parts.append(intro_div.text.strip())
        
        # Helper function to safely extract sections
        def get_section(title: str) -> str:
            section = body.find('h2', string=lambda text: text and text.strip() == title)
            if section:
                next_elem = section.find_next('p') if title != 'Advantages' else section.find_next('ul')
                if next_elem:
                    return f"{title}: {next_elem.get_text(strip=True, separator='. ')}"
            return ""
        
        # Extract each section safely
        for section in ['Technology', 'Problem Addressed', 'Advantages']:
            section_text = get_section(section)
            if section_text:
                description_parts.append(section_text)
        
        # Join all available sections with newlines
        description = "\n\n".join(filter(None, description_parts))
        
        # Get number if available
        header_details = soup.find('div', class_="tech-brief-header__details")
        number = header_details.text.strip().split('\n')[-1].strip() if header_details else ''
        
        return {'description': description, 'number': number}

    def process_item(self, item: Dict[str, str]) -> Dict[str, str]:
        """Process item before adding to dataset"""
        if not item.get('description'):
            item['description'] = 'No description available'
        # Replace newlines with escaped newlines in description
        if 'description' in item:
            item['description'] = item['description'].replace('\n', '\\n')
        return item


if __name__ == '__main__':
    with MITScraper() as scraper:
        try:
            results = scraper.scrape(
                limit=132,  # Number of pages found in notebook
                output_file='data/tech/mit_2024_11_26.csv'
            )
            print(f"Successfully scraped {len(results)} items")
            
        except Exception as e:
            print(f"An error occurred: {str(e)}")
