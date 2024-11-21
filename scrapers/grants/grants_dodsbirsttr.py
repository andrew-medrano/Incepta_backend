import pandas as pd
from bs4 import BeautifulSoup
import requests
import re
import csv
from datetime import datetime

def get_topic_numbers(soup):
    """Extract opportunity numbers from the soup object."""
    return [y.text.strip().split(' ')[0] for y in soup.find_all('div', class_="topic-number-status")]

def get_title(soup):
    """Extract titles from the soup object."""
    return [y.text.strip() for y in soup.find_all('div', class_="topic-title")]

def get_open_date(soup):
    """Extract open date from the soup object."""
    return [y.text.strip() for y in soup.find_all('div', class_="topic-open-close")][0]

def get_close_date(soup):
    """Extract close date from the soup object."""
    return [y.text.strip() for y in soup.find_all('div', class_="topic-open-close")][1]

def get_all_descriptions(soup):
    """
    Get all descriptions from all topics in a page.
    Returns a list of strings, each string is a description.
    """
    detail_text = "\n".join([y.text for y in soup.find_all('div', class_="topicDetailBox container")])
    descriptions = ["KEYWORDS: " + detail_text.split('KEYWORDS')[i] for i in range(1, len(detail_text.split('KEYWORDS')))]
    
    descriptions = [description.replace('OBJECTIVE', '\nOBJECTIVE: ')
                   .replace('DESCRIPTION', '\n\nDESCRIPTION: ')
                   .replace('PHASE III DUAL USE APPLICATIONS', '\n\nPHASE 3 DUAL USE APPLICATIONS: ')
                   .replace('PHASE II', '\n\nPHASE 2: ')
                   .replace('PHASE I', '\n\nPHASE 1: ')
                   for description in descriptions]
    
    return descriptions

def get_funding_from_description(description):
    """Extract funding amount from description using regex."""
    try:
        result =  re.search(r'\$(\d+(,\d{3})*|\d+)', description).group(0)
        if len(result) < 3: # if the result is less than 3 characters, it's probably not a valid number
            return 'nan'
        else:
            return result
    except:
        return 'nan'

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

def process_dod_grants(input_file, output_file=None):
    """Main function to process DOD SBIR/STTR grants data."""
    # Define columns
    columns = [
        'OPPORTUNITY TITLE', 'AGENCY CODE', 'OPPORTUNITY STATUS', 'POSTED DATE', 
        'CLOSE DATE', 'LINK', 'OPPORTUNITY NUMBER', 'CATEGORY', 
        'LAST_UPDATED_DATE', 'POSTED_DATE', 'APPLICATION_DEADLINE', 
        'TOTAL_FUNDING_AMOUNT', 'AWARD_CEILING', 'AWARD_FLOOR', 'DESCRIPTION'
    ]
    
    unused_columns = ['OPPORTUNITY STATUS', 'APPLICATION_DEADLINE', 'CATEGORY', 
                     'LAST_UPDATED_DATE', 'AWARD_CEILING', 'AWARD_FLOOR']
    
    # Read and parse HTML
    with open(input_file, 'r') as file:
        html_content = file.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Set default output filename if none provided
    if output_file is None:
        current_date = datetime.now().strftime('%Y_%m_%d')
        output_file = f'dodsbirsttr_{current_date}.csv'
    
    # Base link for all pages
    link = 'https://www.dodsbirsttr.mil/topics-app/'
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, quoting=csv.QUOTE_ALL)
        writer.writerow([clean_text(col) for col in columns])
        
        titles = get_title(soup)
        topic_numbers = get_topic_numbers(soup)
        open_date = get_open_date(soup)
        close_date = get_close_date(soup)
        descriptions = get_all_descriptions(soup)
        
        for i in range(len(titles)):
            row = []
            for column in columns:
                value = ''
                if column in unused_columns:
                    value = ''
                elif column == 'OPPORTUNITY TITLE':
                    value = titles[i] if i < len(titles) else ''
                elif column == 'AGENCY CODE':
                    value = 'DOD'
                elif column == 'POSTED DATE':
                    value = open_date
                elif column == 'CLOSE DATE':
                    value = close_date
                elif column == 'LINK':
                    value = link
                elif column == 'OPPORTUNITY NUMBER':
                    value = topic_numbers[i] if i < len(topic_numbers) else ''
                elif column == 'DESCRIPTION':
                    value = descriptions[i] if i < len(descriptions) else ''
                elif column == 'TOTAL_FUNDING_AMOUNT':
                    try:
                        if i < len(descriptions):
                            value = get_funding_from_description(descriptions[i])
                        else:
                            value = 'nan'
                    except:
                        value = 'nan'
                
                row.append(clean_text(value))
            writer.writerow(row)

if __name__ == "__main__":
    """
    To use this script, first go to: https://www.dodsbirsttr.mil/topics-app/
    Open all of the dropdowns for all of the topics
    Download the page as HTML
    Run this script, passing in the filename as the argument.
    The output file will be named dodsbirsttr_YYYY_MM_DD.csv, and will be saved in the current working directory.
    """
    process_dod_grants('dodsbirsttr.html', 'dodsbirsttr_2024_11_21.csv')
