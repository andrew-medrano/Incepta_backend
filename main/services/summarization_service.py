import openai
import pandas as pd
from dotenv import load_dotenv
import os
import csv

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')

def truncate_text(text, max_length=1500):
    """Truncate text to a maximum length."""
    return text if len(text) <= max_length else text[:max_length] + '...'

def summarize_text(text, title, content_type='tech', max_tokens=900):
    print(f"\nProcessing summary for: {title[:50]}...")
    
    if not text.strip() or len(text) < 30:
        print("Short/empty text detected - generating brief description from title")
        # Handle cases with only title
        if content_type.lower() == 'grants':
            # Get a brief description from the title using GPT
            brief_desc = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": f"In 15 words or less, what might this grant titled '{title}' be related to? Start with 'supporting' or 'funding'"
                }],
                max_tokens=30
            ).choices[0].message.content.strip()
            
            return (
                "The sponsoring grant agency did not provide a description. "
                f"Based on the title, this grant is likely {brief_desc}.\n\n"
                "For more detailed information about funding objectives, eligibility requirements, "
                "and award amounts, please reach out to learn more about this opportunity."
            )
        else:  # tech case
            # Get a brief description from the title using GPT
            brief_desc = openai.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "user",
                    "content": f"In 15 words or less, what might this technology titled '{title}' be able to do? Start with a verb"
                }],
                max_tokens=30
            ).choices[0].message.content.strip()
            
            return (
                "The institution which posted this technology did not provide a description. "
                f"Based on the title, this technology likely can {brief_desc}.\n\n"
                "If you would like to learn more about the specific capabilities, technical details, "
                "and potential applications of this technology, please reach out to us."
            )

    # Truncate the text to a reasonable length
    text = truncate_text(text)

    if content_type.lower() == 'grants':
        prompt = (
            f"Given the grant titled '{title}', provide a factual summary based only on the available information. "
            "If certain aspects are not mentioned, make reasonable, but conservative assumptions and fill out the summary accordingly. "
            "If this is not possible, indicate 'Information not provided'. Use only sentences, no lists or other formatting. "
            "Do not restate the title in the summary. Start the text and the header on the same line"
            "Use these headers:\n\n"
            f"**Description:**\n\n"
            f"**Research Objectives:**\n\n"
            f"**Expected Outcomes:**\n\n"
            f"**Application Considerations:**\n\n"
            f"Here is the grant description: {text}"
        )
    else:  # tech/default case
        prompt = (
            f"Given the technology titled '{title}', provide a factual summary based only on the available information. "
            "If certain aspects are not mentioned, make reasonable, but conservative assumptions and fill out the summary accordingly. "
            "If this is not possible, indicate 'Information not provided'. Use only sentences, no lists or other formatting. "
            "Do not restate the title in the summary. Start the text and the header on the same line."
            "Use these headers:\n\n"
            f"**Summary:**\n\n"
            f"**Applications:**\n\n"
            f"**Problem Solved:**\n\n"
            f"Here is the technology description: {text}"
        )

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": prompt
        }],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()

def generate_teaser(title, text, max_tokens=100):
    print(f"\nGenerating teaser for: {title[:50]}...")
    
    if not text.strip() or len(text) < 30:
        print("Short/empty text detected - generating teaser from title only")
        # Create a teaser based only on the title
        prompt = (
            f"Create a very brief, factual summary based only on the title: '{title}'. "
            "Do not make assumptions beyond what the title directly implies. "
            "If the title is not descriptive enough, return a conservative statement."
            "Do not restate the title in the summary."
        )
    else:
        prompt = (
            f"Create a brief, factual summary for: '{title}', and the following text: {truncate_text(text, max_length=500)}"
            "Focus only on the clearly stated information in the text. "
            "Avoid speculation. Two sentences max."
            "Do not restate the title in the summary."
        )

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": prompt
        }],
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()

def clean_text(text):
    """Clean text by removing excessive whitespace and normalizing line breaks."""
    if not text:
        return ""
    
    # Convert to string in case we get a non-string input
    text = str(text)
    
    # Replace multiple newlines with a single newline
    text = '\n'.join(line.strip() for line in text.splitlines() if line.strip())
    
    # Replace multiple spaces with a single space
    text = ' '.join(text.split())
    
    return text

def process_csv(input_csv_path, output_csv_path, content_type='tech', limit=None):
    print(f"Starting to process CSV file: {input_csv_path}")
    
    # Load the CSV file
    df = pd.read_csv(input_csv_path, 
                     skipinitialspace=True,  # Skip spaces after delimiter
                     skip_blank_lines=True,  # Skip blank lines
                     encoding='utf-8',       # Specify encoding
                     on_bad_lines='skip',     # Skip problematic lines
                     nrows=limit)
    print(f"Loaded {len(df)} rows from CSV")

    # Clean column names by stripping whitespace
    df.columns = df.columns.str.strip()

    # Find the correct columns using case-insensitive matching
    title_patterns = ['OPPORTUNITY TITLE', 'TITLE']
    desc_patterns = ['DESCRIPTION']
    
    title_col = next((col for col in df.columns 
                     if any(pattern.lower() == col.lower() for pattern in title_patterns)), None)
    description_col = next((col for col in df.columns 
                          if any(pattern.lower() == col.lower() for pattern in desc_patterns)), None)

    if not title_col or not description_col:
        raise ValueError(f"Could not find required columns. Available columns: {df.columns.tolist()}")

    print(f"Using columns: {title_col} and {description_col}")

    # Add new columns for summaries and teasers with improved cleaning
    df['Description'] = df[description_col].apply(clean_text)
    
    print("Starting to generate summaries...")
    df['LLM Summary'] = df.apply(lambda row: 
        summarize_text(row['Description'], row[title_col], content_type), axis=1)
    print("Finished generating summaries")
    
    print("Starting to generate teasers...")
    df['LLM Teaser'] = df.apply(lambda row: 
        generate_teaser(row[title_col], row['Description']), axis=1)
    print("Finished generating teasers")

    # Debugging: Check if 'LLM Teaser' column exists
    print("Columns in DataFrame before saving:", df.columns)

    # Save without any manual newline encoding - let pandas handle it
    print(f"Saving results to: {output_csv_path}")
    df.to_csv(output_csv_path, index=False, quoting=csv.QUOTE_ALL)
    print("Processing complete!")

def read_and_process_csv(file_path, content_type='tech'):
    # Let pandas handle the newline parsing
    df = pd.read_csv(file_path, lineterminator='\n')
    for _, row in df.iterrows():
        print("\n" + "="*80)
        if content_type == 'tech':
            print(f"TECHNOLOGY TITLE: {row['title']}")
            print("-"*80)
            print(f"TECHNICAL DESCRIPTION:\n{row['Description']}")
        else:  # grants
            print(f"GRANT OPPORTUNITY: {row['OPPORTUNITY TITLE']}")
            print("-"*80) 
            print(f"GRANT DESCRIPTION:\n{row['DESCRIPTION']}")
        print("-"*80) 
        print(f"TEASER:\n{row['LLM Teaser']}")
        print("-"*80)
        print(f"SUMMARY:\n{row['LLM Summary']}")

if __name__ == "__main__":
    # Example usage
    input_csv_path = 'Incepta_backend/data/grants/grants_gov_scraped_2024_11_20_cleaned.csv'
    output_csv_path = 'Incepta_backend/data/grants/grants_gov_scraped_2024_11_20_random.csv'
    summarized_csv_path = 'Incepta_backend/data/grants/grants_gov_scraped_2024_11_20_summarized.csv'
    
    # Create random sample
    df = pd.read_csv(input_csv_path)
    random_rows = df.sample(n=10)
    random_rows.to_csv(output_csv_path, index=False)
    
    # Process and summarize
    process_csv(output_csv_path, summarized_csv_path, content_type='grants')
    
    # Read the summarized CSV (not the random sample CSV)
    read_and_process_csv(summarized_csv_path, content_type='grants')
