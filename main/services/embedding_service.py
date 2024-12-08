import pandas as pd
from pinecone import Pinecone, ServerlessSpec
import time
import os
from tqdm import tqdm
from main.constants.categories import CATEGORIES, CATEGORY_DESCRIPTIONS
from main.constants.metadata_fields import (
    TECH_METADATA_FIELDS,
    GRANTS_METADATA_FIELDS,
    COMMON_METADATA_FIELDS
)
import dotenv

dotenv.load_dotenv()

class EmbeddingsGenerator:
    def __init__(self, data_path, index_name):
        self.pc = None
        self.index_name = index_name
        self.data_path = data_path
        self.formatted_data = None
        self.categories = CATEGORIES
        self.category_embeddings = None

    def setup(self):
        print("Setting up Pinecone client...")
        PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Create enhanced category texts that combine name and description
        enhanced_categories = [
            f"{category}: {CATEGORY_DESCRIPTIONS[category]}"
            for category in self.categories
        ]
        
        self.category_embeddings = self.pc.inference.embed(
            model='multilingual-e5-large',
            inputs=enhanced_categories,
            parameters={"input_type": "passage", "truncate": "END"}
        )
        print("Pinecone client and category embeddings setup complete.")

    def create_index(self):
        print(f"Attempting to create index '{self.index_name}'...")
        try:
            self.pc.create_index(
                name=self.index_name,
                dimension=1024,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region="us-east-1"
                )
            )
            print("Index created successfully.")
        except:
            print("Index already exists, skipping creation.")

    def load_data(self, required_cols):
        print("Loading data from CSV...")
        self.df = None
        
        # Separate required and optional columns
        optional_cols = ["LLM Summary", "LLM Teaser"]
        strict_required_cols = [col for col in required_cols if col not in optional_cols]
        
        for file in os.listdir(self.data_path):
            if file.endswith('.csv'):
                print(f"\nLoading {file}...")
                # Add quoting parameter to handle quoted columns
                df = pd.read_csv(
                    os.path.join(self.data_path, file),
                    skipinitialspace=True,
                    quotechar='"',  # Specify quote character
                    encoding='utf-8'
                )
                
                # Clean column names - remove quotes and standardize format
                df.columns = df.columns.str.strip('" ').str.replace(' ', '_').str.upper()
                cleaned_required_cols = [col.strip('" ').replace(' ', '_').upper() for col in strict_required_cols]
                
                print("\nAvailable columns in file:", list(df.columns))
                print("\nCleaned required columns:", cleaned_required_cols)
                
                if not all(col in df.columns for col in cleaned_required_cols):
                    missing_cols = [col for col in cleaned_required_cols if col not in df.columns]
                    print(f"Missing columns: {missing_cols}")
                    continue
                
                if self.df is None:
                    self.df = df
                else:
                    if set(df.columns) == set(self.df.columns):
                        self.df = pd.concat([self.df, df], ignore_index=True)
                    else:
                        print(f"Warning: {file} columns do not match existing dataframe")
                        continue
                
                print(f"{file} loaded. Total rows now: {len(self.df)}")

        if self.df is None:
            raise ValueError("No valid CSV files were loaded. Please check your data files and required columns.")

        self.df.columns = self.df.columns.str.replace(' ', '_')
        print("Column names cleaned.")

    def classify_text(self, text, threshold=0.79):
        """Classify text using vector similarity"""
        text_embedding = self.pc.inference.embed(
            model='multilingual-e5-large',
            inputs=[text],
            parameters={"input_type": "passage", "truncate": "END"}
        )[0]
        
        similarities = []
        for cat_embedding in self.category_embeddings:
            similarity = self._cosine_similarity(
                text_embedding['values'], 
                cat_embedding['values']
            )
            similarities.append(similarity)
        
        categories = [
            self.categories[i] 
            for i, sim in enumerate(similarities) 
            if sim > threshold
        ]
        
        if not categories:
            max_idx = similarities.index(max(similarities))
            categories = [self.categories[max_idx]]
        return categories

    def classify_text_batch(self, texts, threshold=0.79):
        """Classify multiple texts using vector similarity in batch"""
        text_embeddings = self.pc.inference.embed(
            model='multilingual-e5-large',
            inputs=texts,
            parameters={"input_type": "passage", "truncate": "END"}
        )
        
        results = []
        for text_embedding in text_embeddings:
            similarities = []
            for cat_embedding in self.category_embeddings:
                similarity = self._cosine_similarity(
                    text_embedding['values'], 
                    cat_embedding['values']
                )
                similarities.append(similarity)
            
            categories = [
                self.categories[i] 
                for i, sim in enumerate(similarities) 
                if sim > threshold
            ]
            
            if not categories:
                max_idx = similarities.index(max(similarities))
                categories = [self.categories[max_idx]]
            results.append(categories)
        
        return results

    def _cosine_similarity(self, v1, v2):
        """Calculate cosine similarity between two vectors"""
        dot_product = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5
        return dot_product / (norm1 * norm2)

    def format_grants_data(self):
        print("Formatting grants data...")
        data = []
        batch_size = 20
        
        for i in tqdm(range(0, len(self.df), batch_size), desc="Processing grants"):
            batch = self.df.iloc[i:i+batch_size]
            texts_to_classify = []
            
            for _, row in batch.iterrows():
                # Use LLM Summary and Teaser if available, otherwise fall back to original text
                summary = row.get('LLM Summary', '')
                teaser = row.get('LLM Teaser', '')
                title = row.OPPORTUNITY_TITLE if pd.notna(row.OPPORTUNITY_TITLE) else ""
                
                # Combine teaser and summary for classification
                text_for_classification = f"{title} {teaser} {summary}"
                if not summary and not teaser:
                    # Fallback to original description if no LLM content
                    summarized_description = str(row.DESCRIPTION)[:300] if len(str(row.DESCRIPTION)) > 300 else str(row.DESCRIPTION)
                    text_for_classification = f"{title} {summarized_description}"
                
                texts_to_classify.append(text_for_classification)
            
            # Batch classify texts
            batch_categories = self.classify_text_batch(texts_to_classify)
            
            for j, row in enumerate(batch.itertuples(index=False)):
                title = row.OPPORTUNITY_TITLE if pd.notna(row.OPPORTUNITY_TITLE) else ""
                description = row.DESCRIPTION if pd.notna(row.DESCRIPTION) else ""
                
                # Fix: Use standardized column names with underscores
                summary = getattr(row, 'LLM_SUMMARY', '')
                teaser = getattr(row, 'LLM_TEASER', '')
                
                # Text for embedding will be LLM content if available, otherwise original
                embedding_text = f"{title}. {teaser} {summary}" if (summary or teaser) else f"{title}. {description}"
                
                metadata = {
                    "title": title,
                    "opportunity_number": row.OPPORTUNITY_NUMBER if pd.notna(row.OPPORTUNITY_NUMBER) else "",
                    "agency_code": row.AGENCY_CODE if pd.notna(row.AGENCY_CODE) else "",
                    "category": batch_categories[j],
                    "status": row.OPPORTUNITY_STATUS if pd.notna(row.OPPORTUNITY_STATUS) else "",
                    "posted_date": row.POSTED_DATE if pd.notna(row.POSTED_DATE) else "",
                    "last_updated_date": row.LAST_UPDATED_DATE if pd.notna(row.LAST_UPDATED_DATE) else "",
                    "application_deadline": row.APPLICATION_DEADLINE if pd.notna(row.APPLICATION_DEADLINE) else "",
                    "close_date": row.CLOSE_DATE if pd.notna(row.CLOSE_DATE) else "",
                    "total_funding": row.TOTAL_FUNDING_AMOUNT if pd.notna(row.TOTAL_FUNDING_AMOUNT) else "",
                    "award_ceiling": row.AWARD_CEILING if pd.notna(row.AWARD_CEILING) else "",
                    "award_floor": row.AWARD_FLOOR if pd.notna(row.AWARD_FLOOR) else "",
                    "link": row.LINK if pd.notna(row.LINK) else "",
                    "description": description,
                    "llm_summary": summary,
                    "llm_teaser": teaser
                }
                
                data.append({
                    "id": f"vec{i+j}",
                    "text": embedding_text,
                    "metadata": metadata
                })
        
        self.formatted_data = data
        print(f"Processed {len(data)} grants")

    def format_tech_data(self):
        print("Formatting tech data...")
        data = []
        batch_size = 20  # Same batch size as grants
        
        for i in tqdm(range(0, len(self.df), batch_size), desc="Processing tech data"):
            batch = self.df.iloc[i:i+batch_size]
            texts_to_classify = []
            
            for _, row in batch.iterrows():
                summary = row.get('LLM_SUMMARY', '')  # Changed from 'LLM Summary'
                teaser = row.get('LLM_TEASER', '')   # Changed from 'LLM Teaser'
                title = row.TITLE if pd.notna(row.TITLE) else ""  # Changed from row.title

                texts_to_classify.append(f"{title} {teaser} {summary}")
            
            # Batch classify texts
            batch_categories = self.classify_text_batch(texts_to_classify)
            
            for j, row in enumerate(batch.itertuples(index=False)):
                title = row.TITLE if pd.notna(row.TITLE) else ""  # Changed from row.title
                description = row.DESCRIPTION if pd.notna(row.DESCRIPTION) else ""

                # get LLM content using uppercase column names
                summary = getattr(row, 'LLM_SUMMARY', '')  # Changed access method
                teaser = getattr(row, 'LLM_TEASER', '')   # Changed access method
                embedding_text = f"{title} {teaser} {summary}"
                
                data.append({
                    "id": f"{row.UNIVERSITY}-{row.NUMBER}".replace(' ', '_'), # replace spaces with underscores, because id will be used in url
                    "text": embedding_text,
                    "metadata": {
                        "title": title,
                        "university": row.UNIVERSITY if pd.notna(row.UNIVERSITY) else "",  # Changed from row.university
                        "number": row.NUMBER if pd.notna(row.NUMBER) else "",              # Changed from row.number
                        "patent": row.PATENT if pd.notna(row.PATENT) else "",              # Changed from row.patent
                        "link": row.LINK if pd.notna(row.LINK) else "",                    # Changed from row.link
                        "description": description,
                        "category": batch_categories[j],
                        "llm_summary": summary,
                        "llm_teaser": teaser
                    }
                })
        
        self.formatted_data = data
        print(f"Processed {len(data)} tech entries")

    def generate_embeddings(self):
        print("Preparing data for embedding generation...")
        data = self.formatted_data
        print(f"Total items to process: {len(data)}")

        # Process in batches of 90
        batch_size = 20
        all_embeddings = []
        
        for i in tqdm(range(0, len(data), batch_size), desc="Generating embeddings"):
            batch = data[i:i + batch_size]
            batch_embeddings = self.pc.inference.embed(
                model='multilingual-e5-large',
                inputs=[d['text'] for d in batch],
                parameters={"input_type": "passage", "truncate": "END"}
            )
            all_embeddings.extend(batch_embeddings)

        print("Waiting for index to be ready...")
        while not self.pc.describe_index(self.index_name).status['ready']:
            time.sleep(1)
            print(".", end="", flush=True)
        print("\nIndex is ready.")

        index = self.pc.Index(self.index_name)

        print("Preparing vectors for upsert...")
        vectors = []
        MAX_DESC_LENGTH = 30000  # Much more generous limit
        for d, e in zip(data, all_embeddings):
            # Truncate description if present
            if 'description' in d['metadata']:
                d['metadata']['description'] = d['metadata']['description'][:MAX_DESC_LENGTH]
            
            vectors.append({
                "id": d['id'],
                "values": e['values'],
                "metadata": d['metadata']
            })

        print(f"Upserting {len(vectors)} vectors in batches...")
        batch_size = 50  # Smaller batch size for upsert
        for i in tqdm(range(0, len(vectors), batch_size), desc="Upserting vectors"):
            batch = vectors[i:i + batch_size]
            index.upsert(vectors=batch, namespace="ns1")
        print("Upsert complete.")

if __name__ == "__main__":
    option = 'tech' # ONLY CHANGE THIS, DO NOT CHANGE THE REST (grants or tech)
    date = '2024-12-05' # can actually change this too
    options = {
        'grants': {
            'index_name': f'grants-{date}',
            'data_path': 'data/grants',
            'required_cols': [
                "OPPORTUNITY TITLE", "AGENCY CODE", "OPPORTUNITY STATUS",
                "POSTED DATE", "CLOSE DATE", "LINK", "OPPORTUNITY NUMBER",
                "CATEGORY", "LAST_UPDATED_DATE", "POSTED_DATE", "APPLICATION_DEADLINE",
                "TOTAL_FUNDING_AMOUNT", "AWARD_CEILING", "AWARD_FLOOR", "DESCRIPTION",
                "LLM Summary", "LLM Teaser"  # Fixed column names
            ],
            'format_data': 'format_grants_data'
        },
        'tech': {
            'index_name': f'tech-{date}',
            'data_path': 'data/tech',
            'required_cols': ["university", "title", "number", "patent", "link", "description", "LLM Summary", "LLM Teaser"],
            'format_data': 'format_tech_data'
        }
    }

    eg = EmbeddingsGenerator(
        index_name=options[option]['index_name'],
        data_path=options[option]['data_path'],
    )

    print("Starting embedding generation process...")
    eg.setup()
    eg.create_index()
    eg.load_data(options[option]['required_cols'])
    format_method = getattr(eg, options[option]['format_data'])
    format_method()
    eg.generate_embeddings()
    print("Embedding generation process finished.")