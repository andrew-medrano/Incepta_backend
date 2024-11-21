import pandas as pd
import urllib3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from multiprocessing import Pool, cpu_count
import threading
from contextlib import contextmanager
from tenacity import retry, stop_after_attempt, wait_exponential
import logging
import time
import random
from tqdm import tqdm
from functools import partial
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import os
from selenium.webdriver.remote.remote_connection import LOGGER as selenium_logger

urllib3.disable_warnings()
selenium_logger.setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log'),
        logging.StreamHandler()
    ]
)

# Disable all logs from selenium and webdriver-manager
logging.getLogger('WDM').disabled = True
logging.getLogger('selenium').disabled = True
selenium_logger.disabled = True

class BrowserPool:
    def __init__(self, size):
        self.browsers = [self._create_browser() for _ in range(size)]
        self.available = self.browsers.copy()
        self.lock = threading.Lock()
    
    def _create_browser(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        return webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
    
    @contextmanager
    def get_browser(self):
        browser = None
        with self.lock:
            if self.available:
                browser = self.available.pop()
        if browser is None:
            browser = self._create_browser()
        try:
            yield browser
        finally:
            with self.lock:
                if browser in self.browsers:
                    self.available.append(browser)
                else:
                    browser.quit()
    
    def cleanup(self):
        for browser in self.browsers:
            try:
                browser.quit()
            except:
                pass

# Create a global browser pool
browser_pool = BrowserPool(size=max(1, cpu_count() - 1))

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def scrape_grant_details(url, browser=None):
    """Scrape a single grant's details"""
    should_quit = False
    if browser is None:
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        browser = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        should_quit = True
    
    try:
        browser.get(url)
        wait = WebDriverWait(browser, 10)
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        
        rows = browser.find_elements(By.TAG_NAME, "tr")
        data = {}
        
        field_mapping = {
            'Category of Funding Activity:': 'CATEGORY',
            'Last Updated Date:': 'LAST_UPDATED_DATE',
            # Posted date fields
            'Posted Date:': 'POSTED_DATE',
            'Estimated Post Date:': 'POSTED_DATE',
            # Application deadline fields
            'Current Closing Date for Applications:': 'APPLICATION_DEADLINE',
            'Estimated Application Due Date:': 'APPLICATION_DEADLINE',
            'Original Closing Date for Applications:': 'APPLICATION_DEADLINE',
            # Funding fields
            'Estimated Total Program Funding:': 'TOTAL_FUNDING_AMOUNT',
            'Award Ceiling:': 'AWARD_CEILING',
            'Award Floor:': 'AWARD_FLOOR',
            'Description:': 'DESCRIPTION'
        }
        
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) == 2:
                field = cells[0].text.strip()
                
                if field in field_mapping:
                    if field == 'Description:':
                        value = cells[1].text.strip()
                    else:
                        value = cells[1].text.strip()

                    data[field_mapping[field]] = value
        
        return data
    except Exception as e:
        logging.error(f"Error scraping {url}: {str(e)}")
        return None
    finally:
        if should_quit:
            browser.quit()

def process_batch(urls, batch_size=10):
    """Process a batch of URLs using the browser pool"""
    results = []
    with browser_pool.get_browser() as browser:
        # Add progress bar for URLs within each batch
        for url in tqdm(urls, desc="Processing URLs in batch", leave=False):
            try:
                result = scrape_grant_details(url, browser)
                results.append((url, result))
                time.sleep(random.uniform(0.1, 0.2))
            except Exception as e:
                logging.error(f"Error processing {url}: {str(e)}")
                results.append((url, None))
    return results

def main():
    df = pd.read_csv("grants_gov_2024_11_20.csv")
    output_file = "grants_gov_scraped_2024_11_20.csv"
    
    # Check for existing progress
    try:
        existing_df = pd.read_csv(output_file)
        processed_urls = set(existing_df['LINK'])
        df = df[~df['LINK'].isin(processed_urls)].copy()
        logging.info(f"Resuming processing. {len(processed_urls)} entries already processed.")
    except FileNotFoundError:
        logging.info("Starting fresh processing.")
    
    if len(df) == 0:
        logging.info("All entries have been processed!")
        return

    # Define columns with their proper dtypes
    column_dtypes = {
        'CATEGORY': 'object',
        'LAST_UPDATED_DATE': 'object',
        'POSTED_DATE': 'object',
        'APPLICATION_DEADLINE': 'object',
        'TOTAL_FUNDING_AMOUNT': 'object',
        'AWARD_CEILING': 'object',
        'AWARD_FLOOR': 'object',
        'DESCRIPTION': 'object'
    }
    
    # Initialize new columns with correct dtypes
    for col, dtype in column_dtypes.items():
        if col not in df.columns:
            df[col] = pd.Series(dtype=dtype)
    
    # Add overall progress information
    total_entries = len(df)
    logging.info(f"Starting to process {total_entries} entries")
    
    # Process in parallel batches
    batch_size = 10
    num_processes = max(1, cpu_count() - 1)
    url_batches = [df['LINK'].iloc[i:i + batch_size].tolist() 
                  for i in range(0, len(df), batch_size)]
    
    # Add progress bar for overall batch processing
    with Pool(num_processes) as pool:
        results = list(tqdm(
            pool.imap(process_batch, url_batches),
            total=len(url_batches),
            desc="Processing batches",
            position=0
        ))
    
    # Add progress bar for results processing
    logging.info("Processing results and updating DataFrame...")
    for batch_results in tqdm(results, desc="Updating DataFrame"):
        for url, grant_data in batch_results:
            if grant_data:
                idx = df[df['LINK'] == url].index[0]
                for col in column_dtypes.keys():
                    value = grant_data.get(col)
                    if value is not None:
                        if column_dtypes[col] == 'float64':
                            if isinstance(value, str):
                                value = value.replace('$', '').replace(',', '').strip()
                                try:
                                    value = float(value)
                                except ValueError:
                                    value = None
                        df.loc[idx, col] = value
    
    # Save final results
    if os.path.exists(output_file):
        final_df = pd.concat([pd.read_csv(output_file), df])
        final_df.to_csv(output_file, index=False)
    else:
        df.to_csv(output_file, index=False)
    
    logging.info("Scraping completed successfully")

if __name__ == "__main__":
    try:
        main()
    finally:
        browser_pool.cleanup()
