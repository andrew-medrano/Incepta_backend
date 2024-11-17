from base_scraper import BaseScraper
from bs4 import BeautifulSoup
import time
from typing import List, Dict

class StanfordScraper(BaseScraper):
    """Scraper for Stanford TechFinder website"""

    def __init__(self):
        super().__init__("https://techfinder.stanford.edu/")

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
            items.append({
                'title': title.text.strip(),
                'link': self.base_url[:-1] + title.find('a')['href']
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
        soup = BeautifulSoup(response.content, 'html.parser')
        time.sleep(0.1)  # Be polite and avoid overloading the server
        
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
            if applications_header:
                applications = [li.get_text() for li in applications_header.find_next('ul').find_all('li')]

            # Get advantages
            advantages_header = subpage_soup.find('h2', string="Advantages")
            advantages = []
            if advantages_header:
                advantages = [li.get_text() for li in advantages_header.find_next('ul').find_all('li')]
            
            # Get descriptions
            descriptions = [
                para.get_text().strip() 
                for para in subpage_soup.find('div', class_='docket__text').find_all('p')
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
            print(f"Error extracting description: {str(e)}")
            return "Description not available"


def main():
    """Main function to run the scraper"""
    import argparse

    parser = argparse.ArgumentParser(description="Stanford TechFinder Scraper")
    parser.add_argument("output_file", help="Path to save the output CSV file")
    args = parser.parse_args()

    print("Starting Stanford TechFinder scraping process...")
    limit = 133 # Number of pages to scrape
    output_file = args.output_file
    
    with StanfordScraper() as scraper:
        scraper.scrape(limit=limit, output_file=output_file)
    
    print(f"Data saved to {output_file}")


if __name__ == "__main__":
    main()
