from scrapers.tech.base_scraper import BaseScraper
from bs4 import BeautifulSoup
import time
from typing import List, Dict, Optional
import logging
import aiohttp
import asyncio
from aiohttp import ClientSession
from async_timeout import timeout
from ratelimit import limits, sleep_and_retry

class StanfordScraper(BaseScraper):
    """Scraper for Stanford TechFinder website"""

    def __init__(self):
        fieldnames = ["university", "title", "number", "patent", "link", "description"]
        headers = {
            'User-Agent': 'StanfordScraper/1.0 (research@joinincepta.com)'
        }
        super().__init__(
            base_url="https://techfinder.stanford.edu/",
            fieldnames=fieldnames,
            headers=headers
        )
        self.university_name = "Stanford University"
        self.rate_limit = 10  # requests per second

    async def get_page_soup(self, session: ClientSession, page_number: int) -> BeautifulSoup:
        """
        Fetch and parse HTML content from a single page, given a page number

        Args:
            session (ClientSession): The HTTP session to use for requests.
            page_number (int): The page number to fetch.

        Returns:
            BeautifulSoup: Parsed HTML content of the page.
        """
        url = f"{self.base_url}?page={page_number}"
        async with session.get(url) as response:
            content = await response.text()
            return BeautifulSoup(content, 'html.parser')

    def get_items_from_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        Extract items (titles and links) from a page.

        Args:
            soup (BeautifulSoup): Parsed HTML content of a page.

        Returns:
            List[Dict[str, str]]: List of dictionaries containing title and link for each item.
        """
        titles = soup.find_all('h3', class_='teaser__title')
        items = []
        for title in titles:
            link_element = title.find('a')
            if link_element and link_element.get('href'):
                items.append({
                    'university': self.university_name,
                    'title': title.text.strip(),
                    'link': self.make_absolute_url(link_element['href'])
                })
        return items

    async def get_item_details(self, session: ClientSession, link: str) -> Dict[str, str]:
        """
        Get detailed information for a single item.

        Args:
            session (ClientSession): The HTTP session to use for requests.
            link (str): URL of the item's page.

        Returns:
            Dict[str, str]: Dictionary containing the item's details.
        """
        async with session.get(link) as response:
            content = await response.text()
            soup = BeautifulSoup(content, 'html.parser')
            await asyncio.sleep(0.1)
            
            number = soup.find('div', class_='node__eyebrow docket__eyebrow').text.strip()
            patent_header = soup.find('h2', string='Patents')
            if patent_header and patent_header.find_next('ul'):
                patents = [li.get_text().strip() for li in patent_header.find_next('ul').find_all('li')]
                patents = ", ".join([x.replace('\n', ' ') for x in patents])
            else:
                patents = None
            description = self.get_description(soup)
            
            return {
                'number': clean_text(number),
                'patent': clean_text(patents),
                'description': clean_text(description)
            }

    def get_description(self, subpage_soup: BeautifulSoup) -> str:
        """
        Extract and format applications and advantages from a subpage, even when description is missing.

        Args:
            subpage_soup (BeautifulSoup): Parsed HTML content of a subpage.

        Returns:
            str: Formatted text including applications and advantages, with description if available.
        """
        try:
            # Get applications
            applications_header = subpage_soup.find('h2', string='Applications')
            applications = []
            if applications_header and applications_header.find_next('ul'):
                applications = [li.get_text().strip() for li in applications_header.find_next('ul').find_all('li')]

            # Get advantages
            advantages_header = subpage_soup.find('h2', string='Advantages')
            advantages = []
            if advantages_header and advantages_header.find_next('ul'):
                advantages = [li.get_text().strip() for li in advantages_header.find_next('ul').find_all('li')]
            
            # Get descriptions (if available)
            description_div = subpage_soup.find('div', class_='docket__text')
            descriptions = []
            if description_div:
                descriptions = [
                    para.get_text().strip() 
                    for para in description_div.find_all('p')
                    if para.get_text().strip()
                ]

            # Construct the final paragraph, only including non-empty sections
            parts = []
            if descriptions:
                parts.append("\n".join(descriptions))
            if applications:
                parts.append(f'Applications: {", ".join(applications)}.')
            if advantages:
                parts.append(f'Advantages: {", ".join(advantages)}.')

            # If we have any content, join it; otherwise return a default message
            if parts:
                return "\n\n".join(parts)
            return "No description, applications, or advantages available"

        except Exception as e:
            logging.error(f"Error extracting description: {str(e)}")
            return "Error extracting content"

    async def scrape(self, limit: int = None, output_file: Optional[str] = None, max_concurrent: int = 5) -> List[Dict[str, str]]:
        # Your Stanford-specific scraping implementation
        return await super().scrape(limit=limit, output_file=output_file, max_concurrent=max_concurrent)


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

async def main():
    """Main function to run the scraper"""
    print("Starting Stanford TechFinder scraping process...")
    
    async with StanfordScraper() as scraper:
        await scraper.scrape(output_file='data/tech/stanford_2024_11_24.csv')

if __name__ == "__main__":
    asyncio.run(main())
