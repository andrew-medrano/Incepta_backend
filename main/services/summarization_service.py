import openai
import pandas as pd
from dotenv import load_dotenv
import os

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
            "If this is not possible, indicate 'Information not provided'. "
            "Use these headers:\n\n"
            f"Award Information:\n\n"
            f"Potential Applications:\n\n"
            f"Text: {text}"
        )
    else:  # tech/default case
        prompt = (
            f"Given the technology titled '{title}', provide a factual summary based only on the available information. "
            "If certain aspects are not mentioned, make reasonable, but conservative assumptions and fill out the summary accordingly. "
            "If this is not possible, indicate 'Information not provided'. "
            "Use these headers:\n\n"
            f"Summary:\n\n"
            f"Applications:\n\n"
            f"Problem Solved:\n\n"
            f"Text: {text}"
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
            f"Create a very brief, factual summarybased only on the title: '{title}'. "
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

def process_csv(input_csv_path, output_csv_path, content_type='tech', limit=None):
    print(f"Starting to process CSV file: {input_csv_path}")
    
    # Load the CSV file
    df = pd.read_csv(input_csv_path, nrows=limit)
    print(f"Loaded {len(df)} rows from CSV")

    # Determine the correct column names for title and description
    title_col = 'OPPORTUNITY TITLE' if content_type.lower() == 'grants' else 'title'
    description_col = 'DESCRIPTION' if content_type.lower() == 'grants' else 'description'
    print(f"Using columns: {title_col} and {description_col}")

    # Add new columns for summaries and teasers
    df['Description'] = df[description_col]
    
    print("Starting to generate summaries...")
    df['LLM Summary'] = df.apply(lambda row: 
        summarize_text(row['Description'], row[title_col], content_type).replace('\n', '\\n'), axis=1)
    print("Finished generating summaries")
    
    print("Starting to generate teasers...")
    df['LLM Teaser'] = df.apply(lambda row: 
        generate_teaser(row[title_col], row['Description']).replace('\n', '\\n'), axis=1)
    print("Finished generating teasers")

    # Save the updated DataFrame to a new CSV file with proper quoting
    print(f"Saving results to: {output_csv_path}")
    df.to_csv(output_csv_path, index=False, quoting=1, escapechar='\\')  # quoting=1 is QUOTE_ALL
    print("Processing complete!")


if __name__ == "__main__":
    # Example usage
    # Read 3 random rows
    df = pd.read_csv('Incepta_backend/data/tech/mit_2024_11_26.csv')
    random_rows = df.sample(n=3)
    random_rows.to_csv('Incepta_backend/data/tech/mit_2024_11_26_random.csv', index=False)
    process_csv('Incepta_backend/data/tech/mit_2024_11_26_random.csv', 'Incepta_backend/data/tech/mit_2024_11_26_summarized.csv')
    # Read the summarized CSV and print results
    df_results = pd.read_csv('Incepta_backend/data/tech/mit_2024_11_26_summarized.csv')
    for _, row in df_results.iterrows():
        print("\n" + "="*80)
        print(f"TITLE: {row['title']}")
        print("-"*80)
        print(f"DESCRIPTION:\n{row['Description'].replace('\\n', '\n')}")
        print("-"*80) 
        print(f"TEASER:\n{row['LLM Teaser'].replace('\\n', '\n')}")
        print("-"*80)
        print(f"SUMMARY:\n{row['LLM Summary'].replace('\\n', '\n')}")