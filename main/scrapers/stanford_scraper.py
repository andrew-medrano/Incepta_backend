# Full scraper for Stanford TechFinder

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from typing import List, Dict
import csv
from tqdm import tqdm

base_url = "https://techfinder.stanford.edu/"

def get_all_pages_soups(limit: int = 130) -> List[BeautifulSoup]:
    """
    Fetch and parse HTML content from multiple pages of Stanford TechFinder.

    Args:
        limit (int): Maximum number of pages to fetch. Defaults to 130.

    Returns:
        List[BeautifulSoup]: List of BeautifulSoup objects, each representing a page.
    """
    num_pages = min(limit, 130)
    soups = []
    for page in range(num_pages):
        url = f"{base_url}?page={page}"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        soups.append(soup)
        time.sleep(1)  # Be polite and avoid overloading the server
        print(f"Fetched page {page + 1} of {num_pages}")
    return soups

def get_titles_from_page_soup(soup: BeautifulSoup) -> List[str]:
    """
    Extract titles from a BeautifulSoup object of a TechFinder page.

    Args:
        soup (BeautifulSoup): Parsed HTML content of a page.

    Returns:
        List[str]: List of titles extracted from the page.
    """
    titles = soup.find_all('h3', class_='teaser__title')
    return [title.text.strip() for title in titles]

def get_links_from_page_soup(soup: BeautifulSoup) -> List[str]:
    """
    Extract links from a BeautifulSoup object of a TechFinder page.

    Args:
        soup (BeautifulSoup): Parsed HTML content of a page.

    Returns:
        List[str]: List of links extracted from the page.
    """
    links = [base_url[:-1] + title.find('a')['href'] for title in soup.find_all('h3', class_='teaser__title')]
    return links

def get_subpage_soup(link: str) -> BeautifulSoup:
    """
    Fetch and parse HTML content from a subpage link.

    Args:
        link (str): URL of the subpage.

    Returns:
        BeautifulSoup: Parsed HTML content of the subpage.
    """
    response = requests.get(link)
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup

def get_description(subpage_soup: BeautifulSoup):
    """
    Extract and format description, applications, and advantages from a subpage.

    Args:
        subpage_soup (BeautifulSoup): Parsed HTML content of a subpage.

    Returns:
        str: Formatted description including applications and advantages.
    """
    # Get applications and advantages
    applications = [li.get_text() for li in subpage_soup.find('h2', string="Applications").find_next('ul').find_all('li')]
    advantages = [li.get_text() for li in subpage_soup.find('h2', string="Advantages").find_next('ul').find_all('li')]
    
    # Get descriptions
    descriptions = [para.get_text().strip() for para in subpage_soup.find('div', class_='docket__text').find_all('p')]
    full_description = " ".join(descriptions)

    # Construct the final paragraph with applications and advantages
    full_paragraph = f"{full_description} Applications include {', '.join(applications)}. Advantages of the device are {', '.join(advantages)}."

    # Remove any newlines
    full_paragraph = full_paragraph.replace('\n', ' ')
    return full_paragraph

def scrape_page(session: requests.Session, page_number: int) -> List[Dict[str, str]]:
    """
    Scrape a single page from Stanford TechFinder website.

    Args:
        session (requests.Session): The session to use for requests.
        page_number (int): The page number to scrape.

    Returns:
        List[Dict[str, str]]: List of dictionaries containing scraped data.
    """
    url = f"{base_url}?page={page_number}"
    response = session.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    titles = get_titles_from_page_soup(soup)
    links = get_links_from_page_soup(soup)
    
    page_data = []
    with tqdm(total=len(titles), desc=f"Page {page_number + 1}", leave=False) as item_pbar:
        for title, link in zip(titles, links):
            try:
                subpage_soup = get_subpage_soup(link)
                description = get_description(subpage_soup)
                
                page_data.append({
                    "title": title,
                    "link": link,
                    "description": description,
                })
            except Exception as e:
                print(f"Error processing {link}: {str(e)}")
            
            time.sleep(0.1)  # Be polite and avoid overloading the server
            item_pbar.update(1)
    
    return page_data

def scrape_techfinder(limit: int = 130, output_file: str = "data/stanford_techfinder.csv") -> None:
    """
    Scrape Stanford TechFinder website and save data to a CSV file.

    Args:
        limit (int): Maximum number of pages to scrape. Defaults to 130.
        output_file (str): Path to the output CSV file. Defaults to "data/stanford_techfinder.csv".
    """
    with requests.Session() as session, open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["title", "link", "description"])
        writer.writeheader()

        with tqdm(total=limit, desc="Scraping pages") as pbar:
            for i in range(limit):
                try:
                    page_data = scrape_page(session, i)
                    writer.writerows(page_data)
                    csvfile.flush()  # Ensure data is written to disk
                except Exception as e:
                    print(f"Error scraping page {i}: {str(e)}")
                    print("Saving progress and exiting...")
                    break
                pbar.update(1)

if __name__ == "__main__":
    print("Starting scraping process...")
    limit = 133
    scrape_techfinder(limit=limit, output_file=f"data/stanford_techfinder_{limit}_pages.csv")
    print(f"Data saved to stanford_techfinder_{limit}_pages.csv")
