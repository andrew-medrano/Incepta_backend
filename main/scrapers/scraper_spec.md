# Web Scraper Implementation Guide
author: Andrew Medrano 

email: andrew.medrano@gmail.com

date: November 20, 2024

## Table of Contents
- [Web Scraper Implementation Guide](#web-scraper-implementation-guide)
  - [Table of Contents](#table-of-contents)
  - [Project Structure and Setup](#project-structure-and-setup)
    - [Directory Structure](#directory-structure)
    - [Environment Setup](#environment-setup)
      - [Prerequisites](#prerequisites)
      - [Setup Instructions](#setup-instructions)
    - [Contributing](#contributing)
      - [Prerequisites](#prerequisites-1)
      - [Development Workflow](#development-workflow)
  - [Overview](#overview)
  - [Data Requirements](#data-requirements)
  - [Base Class Structure](#base-class-structure)
  - [Key Components to Implement](#key-components-to-implement)
    - [Class Definition](#class-definition)
    - [Required Methods](#required-methods)
      - [get\_page\_soup](#get_page_soup)
      - [get\_items\_from\_page](#get_items_from_page)
      - [get\_item\_details](#get_item_details)
  - [Adding New Scrapers](#adding-new-scrapers)
  - [Running Scrapers](#running-scrapers)
  - [Best Practices and Tips](#best-practices-and-tips)
    - [HTML Inspection](#html-inspection)
    - [Rate Limiting](#rate-limiting)
    - [Error Handling and Logging](#error-handling-and-logging)
    - [Data Storage](#data-storage)
    - [BeautifulSoup Quick Reference](#beautifulsoup-quick-reference)
    - [Final Checklist](#final-checklist)
    - [Git Workflow and Pull Requests](#git-workflow-and-pull-requests)
      - [Branching Strategy](#branching-strategy)
      - [Pull Request Process](#pull-request-process)
    - [Support](#support)

## Project Structure and Setup



### Directory Structure
The project follows this directory structure for organization and consistency:
```
Incepta_backend/
|-- README.md          # Project overview and setup instructions
|-- requirements.txt   # Python package dependencies
|-- main/
|   |-- scrapers/     # All web scrapers go here
|   |   |-- base_scraper.py
|   |   |-- your_scraper.py
|   |-- static/
|   |   |-- images/   # Static assets
|   |-- templates/    # Web interface templates
|   |-- embeddings_generator.py
|   |-- semantic_search_app.py
|   |-- semantic_llm_search.py
|-- data/
    |-- tech/        # Scraped technology data goes here
        |-- stanford_2024_11_20.csv
    |-- grants/
        |-- grants_sbir_2024_11_20.csv
```

### Environment Setup
#### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git

#### Setup Instructions
1. Create and activate a virtual environment:
    ```bash
    # On Windows
    python -m venv venv
    .\venv\Scripts\activate

    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

2. Install required packages:
    ```bash
    pip install -r requirements.txt
    ```

### Contributing

#### Prerequisites
1. Create a GitHub account if you don't have one
2. Fork the repository by clicking the "Fork" button at https://github.com/andrew-medrano/Incepta_backend
3. Clone your fork (not the original repository):
    ```bash
    git clone https://github.com/YOUR-USERNAME/Incepta_backend.git
    cd Incepta_backend
    ```
4. Add the original repository as a remote named "upstream":
    ```bash
    git remote add upstream https://github.com/andrew-medrano/Incepta_backend.git
    ```

#### Development Workflow
1. Keep your fork up to date:
    ```bash
    git checkout develop
    git fetch upstream
    git merge upstream/develop
    git push origin develop
    ```

2. Create your feature branch:
    ```bash
    git checkout -b feature/your-university-scraper
    ```

3. Make your changes and commit them:
    ```bash
    git add .
    git commit -m "feat: Add scraper for University Name"
    ```

4. Push to your fork:
    ```bash
    git push origin feature/your-university-scraper
    ```

5. Create a Pull Request:
   - Go to https://github.com/andrew-medrano/Incepta_backend
   - Click "New Pull Request"
   - Click "compare across forks"
   - Select your fork and branch
   - Fill in the PR template with required information

## Overview
This guide explains how to create new web scrapers that inherit from the updated **BaseScraper** class. The goal is to collect technology listings from university technology transfer offices and compile them into a structured dataset.

## Data Requirements
The data collected by the scraper should be assembled into a DataFrame with the following columns:
\begin{itemize}
    \item \textbf{university}: Name of the university
    \item \textbf{title}: Title of the technology listing
    \item \textbf{link}: URL to the detailed technology page
    \item \textbf{description}: Detailed description of the technology, including application areas, benefits, and other relevant information
\end{itemize}

## Base Class Structure
The **BaseScraper** class provides a robust foundation for implementing website-specific scrapers. It includes:
\begin{itemize}
    \item Session management with customizable headers
    \item Abstract methods that must be implemented in subclasses
    \item Flexible data field configuration
    \item Error handling and logging
    \item Optional retry logic for network requests
    \item Data collection and assembly into a DataFrame
\end{itemize}

## Key Components to Implement

### Class Definition
Your scraper should inherit from **BaseScraper** and initialize with the target website's URL, university name, and required data fields.

```python
from base_scraper import BaseScraper
from bs4 import BeautifulSoup
from typing import List, Dict
import time
import logging

class YourWebsiteScraper(BaseScraper):
    def __init__(self):
        fieldnames = ["university", "title", "link", "description"]
        super().__init__(
            base_url="https://your-website-url.com/",
            fieldnames=fieldnames,
            headers={
                'User-Agent': 'YourScraperName/1.0 (contact@example.com)'
            }
        )
        self.university = "Your University Name"
```

### Required Methods

#### get\_page\_soup
```python
@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def get_page_soup(self, page_number: int) -> BeautifulSoup:
    """
    Fetch and parse HTML content from a single page.
    
    Args:
        page_number (int): The page number to fetch.
    
    Returns:
        BeautifulSoup: Parsed HTML content of the page.
    """
    url = f"{self.base_url}/listings?page={page_number}"
    response = self.session.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    time.sleep(1)
    return soup
```

#### get\_items\_from\_page
```python
def get_items_from_page(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
    """
    Extract items from a page.
    
    Args:
        soup (BeautifulSoup): Parsed HTML content of a page.
    
    Returns:
        List[Dict[str, str]]: List of items with their titles and links.
    """
    items = []
    listings = soup.find_all('div', class_='listing-item')
    
    for listing in listings:
        title_element = listing.find('h3', class_='title')
        link_element = listing.find('a', class_='details-link')
        
        if title_element and link_element:
            title = title_element.get_text(strip=True)
            link = self.make_absolute_url(link_element['href'])
            items.append({
                'university': self.university,
                'title': title,
                'link': link
            })
        else:
            logging.warning(f"Missing title or link in listing: {listing}")
    
    return items
```

#### get\_item\_details
```python
def get_item_details(self, link: str) -> Dict[str, str]:
    """
    Get detailed information for a single item.
    
    Args:
        link (str): URL of the item's page.
    
    Returns:
        Dict[str, str]: Dictionary containing item details.
    """
    response = self.session.get(link)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    time.sleep(0.5)
    
    description_element = soup.find('div', class_='description')
    description = description_element.get_text(strip=True) if description_element else ''
    description = self.clean_text(description)
    
    return {'description': description}
```

## Adding New Scrapers
When adding a new scraper:

1. Create a new file in \texttt{main/scrapers/} with your scraper class
2. Follow the naming convention: \texttt{university\_name\_scraper.py}
3. Ensure scraped data is saved to \texttt{data/tech/}
4. Update \texttt{requirements.txt} if new dependencies are needed

## Running Scrapers
1. Ensure you're in the project root directory
2. Activate the virtual environment
3. Run your scraper:
    ```bash
    python -m main.scrapers.your_scraper \
    --output data/tech/university_name_$(date +%Y_%m_%d).csv \
    ```

## Best Practices and Tips

### HTML Inspection
1. Use browser developer tools (F12) to inspect website HTML
2. Look for unique class names or IDs
3. Test selectors in browser console first

### Rate Limiting
1. Include \texttt{time.sleep()} delays between requests
2. Start with conservative delays (e.g., 1 second)
3. Check the website's robots.txt for guidance

### Error Handling and Logging
1. Use try/except blocks for critical sections
2. Use \texttt{response.raise\_for\_status()} to handle HTTP errors
3. Provide fallback values when data extraction fails
4. Use the logging module for appropriate severity levels

### Data Storage
1. All scraped data should be saved in the \texttt{data/tech/} directory
2. Use consistent naming: \texttt{university\_name\_YYYY\_MM\_DD.csv}
3. Include metadata in the CSV header when possible
4. Ensure proper encoding (UTF-8) for all saved files

### BeautifulSoup Quick Reference
Documentation: https://www.crummy.com/software/BeautifulSoup/bs4/doc/ 

Common selectors:
```python
soup.find('tag_name', class_='class_name')
soup.find_all('tag_name', class_='class_name')
element.get_text(strip=True)
element['attribute_name']
element.find_next('tag_name')
element.find_parent('tag_name')
```

### Final Checklist
1. Included 'university' Field
2. Verified Data Fields
3. Ensured Proper Error Handling
4. Tested Scraper with Multiple Pages
5. Output Data Matches Specified Format
6. Complied with Ethical Scraping Practices
7. Handled Missing Data
8. Used Absolute URLs
9. Set Custom Headers
10. Validated Data
11. Documented Code

### Git Workflow and Pull Requests

#### Branching Strategy
1. Main Branches:
   - `main`: Production-ready code
   - `develop`: Integration branch for features

2. Feature Branches:
   - Name format: `feature/university-name-scraper`
   - Branch from: `develop`
   - Merge to: `develop`

3. Hotfix Branches:
   - Name format: `hotfix/brief-description`
   - Branch from: `main`
   - Merge to: both `main` and `develop`

#### Pull Request Process
1. Create a new branch:
    ```bash
    git checkout develop
    git pull origin develop
    git checkout -b feature/your-university-scraper
    ```

2. Commit your changes:
    ```bash
    git add .
    git commit -m "feat: Add scraper for University Name"
    ```

3. Push and create PR:
    ```bash
    git push origin feature/your-university-scraper
    ```

4. PR Requirements:
   - Title follows format: "feat: Add scraper for University Name"
   - Description includes:
     - Brief overview of changes
     - Testing methodology
     - Sample of scraped data
   - All tests passing
   - Code follows style guide
   - Documentation updated

5. Review Process:
   - At least one approval required
   - All comments addressed

### Support
If you encounter issues:

1. Verify HTML Structure
2. Check Selector Accuracy
3. Test Edge Cases
4. Handle HTTP Errors
5. Update Selectors as needed


Contact the development team if you need additional assistance via GitHub issues at:
[https://github.com/andrew-medrano/Incepta_backend/issues](https://github.com/andrew-medrano/Incepta_backend/issues)
