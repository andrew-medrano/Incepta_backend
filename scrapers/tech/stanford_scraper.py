from Incepta_backend.scrapers.tech.base_scraper import BaseScraper
from bs4 import BeautifulSoup
import time
from typing import List, Dict
import logging

class StanfordScraper(BaseScraper):
    """Scraper for Stanford TechFinder website"""

    def __init__(self):
        fieldnames = ['university', 'title', 'description', 'link']
        headers = {
            'User-Agent': 'StanfordScraper/1.0 (research@joinincepta.com)'
        }
        super().__init__(
            base_url="https://techfinder.stanford.edu/",
            fieldnames=fieldnames,
            headers=headers
        )
        self.university_name = "Stanford University"

    def get_page_soup(self, page_number: int) -> BeautifulSoup:
        """
        Fetch and parse HTML content from a single page.

        Args:
            page_number (int): The page number to fetch.

        Returns:
            BeautifulSoup: Parsed HTML content of the page.
        """
        url = f"{self.base_url}?page={page_number}"
        response = self.session.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        soup = BeautifulSoup(response.content, 'html.parser')
        time.sleep(1)  # Be polite and avoid overloading the server
        return soup

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

    def get_item_details(self, link: str) -> Dict[str, str]:
        """
        Get detailed information for a single item.

        Args:
            link (str): URL of the item's page.

        Returns:
            Dict[str, str]: Dictionary containing the item's description.
        """
        response = self.session.get(link)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        time.sleep(0.5)  # Increased delay to be more conservative
        
        description = self.get_description(soup)
        return {'description': description}

    def get_description(self, subpage_soup: BeautifulSoup) -> str:
        """
        Extract and format description, applications, and advantages from a subpage.

        Args:
            subpage_soup (BeautifulSoup): Parsed HTML content of a subpage.

        Returns:
            str: Formatted description including applications and advantages.
        """
        try:
            # Get applications
            applications_header = subpage_soup.find('h2', string="Applications")
            applications = []
            if applications_header and applications_header.find_next('ul'):
                applications = [li.get_text().strip() for li in applications_header.find_next('ul').find_all('li')]

            # Get advantages
            advantages_header = subpage_soup.find('h2', string="Advantages")
            advantages = []
            if advantages_header and advantages_header.find_next('ul'):
                advantages = [li.get_text().strip() for li in advantages_header.find_next('ul').find_all('li')]
            
            # Get descriptions
            description_div = subpage_soup.find('div', class_='docket__text')
            if not description_div:
                return "Description not available"
                
            descriptions = [
                para.get_text().strip() 
                for para in description_div.find_all('p')
                if para.get_text().strip()
            ]
            full_description = " ".join(descriptions)

            # Construct the final paragraph
            parts = [full_description]
            if applications:
                parts.append(f"Applications include {', '.join(applications)}.")
            if advantages:
                parts.append(f"Advantages of the device are {', '.join(advantages)}.")

            full_paragraph = " ".join(parts)

            # Remove any newlines and extra spaces
            return ' '.join(full_paragraph.replace('\n', ' ').split())

        except Exception as e:
            logging.error(f"Error extracting description: {str(e)}")
            return "Description not available"


def main():
    """Main function to run the scraper"""
    import argparse

    parser = argparse.ArgumentParser(description="Stanford TechFinder Scraper")
    parser.add_argument("output_file", help="Path to save the output CSV file")
    parser.add_argument("--limit", type=int, default=133, help="Number of pages to scrape")
    args = parser.parse_args()

    print("Starting Stanford TechFinder scraping process...")
    
    with StanfordScraper() as scraper:
        scraper.scrape(limit=args.limit, output_file=args.output_file)
    
    print(f"Data saved to {args.output_file}")


if __name__ == "__main__":
    main()
