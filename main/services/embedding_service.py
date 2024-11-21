import pandas as pd
from pinecone import Pinecone, ServerlessSpec
import time
import os

class EmbeddingsGenerator:
    def __init__(self, data_path, index_name, batch_start = 0):
        self.pc = None
        self.index_name = index_name
        self.data_path = data_path
        self.batch_start = batch_start
        self.formatted_data = None

    def setup(self):
        print("Setting up Pinecone client...")
        PINECONE_API_KEY = open("/Users/andre/startup/pinecone_api_key.txt", "r").read()
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        print("Pinecone client setup complete.")

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
        # Initialize self.df as None at the start
        self.df = None
        
        for file in os.listdir(self.data_path):
            if file.endswith('.csv'):
                print(f"Loading {file}...")
                df = pd.read_csv(os.path.join(self.data_path, file))

                if not all(col in df.columns for col in required_cols):
                    print(f"Warning: {file} missing required columns {required_cols}")
                    continue
                
                # Update initialization logic
                if self.df is None:
                    self.df = df
                else:
                    # Append only if columns match
                    if set(df.columns) == set(self.df.columns):
                        self.df = pd.concat([self.df, df], ignore_index=True)
                    else:
                        print(f"Warning: {file} columns do not match existing dataframe")
                        continue
                
                print(f"{file} loaded. Total rows now: {len(self.df)}")

        # Check if any data was loaded
        if self.df is None:
            raise ValueError("No valid CSV files were loaded. Please check your data files and required columns.")

        # Clean column names
        self.df.columns = self.df.columns.str.replace(' ', '_')
        print("Column names cleaned.")

    def format_grants_data(self):
        data = [
            {
                "id": f"vec{i}",
                "text": f"{row.OPPORTUNITY_TITLE}. " + \
                       (f"Number: {row.OPPORTUNITY_NUMBER}. " if pd.notna(row.OPPORTUNITY_NUMBER) and row.OPPORTUNITY_NUMBER != '' else '') + \
                       (f"\nAgency: {row.AGENCY_CODE}. " if pd.notna(row.AGENCY_CODE) and row.AGENCY_CODE != '' else '') + \
                       (f"\nCategory: {row.CATEGORY}. " if pd.notna(row.CATEGORY) and row.CATEGORY != '' else '') + \
                       (f"\nStatus: {row.OPPORTUNITY_STATUS}. " if pd.notna(row.OPPORTUNITY_STATUS) and row.OPPORTUNITY_STATUS != '' else '') + \
                       (f"\nPosted: {row.POSTED_DATE}. " if pd.notna(row.POSTED_DATE) and row.POSTED_DATE != '' else '') + \
                       (f"\nLast Updated: {row.LAST_UPDATED_DATE}. " if pd.notna(row.LAST_UPDATED_DATE) and row.LAST_UPDATED_DATE != '' else '') + \
                       (f"\nApplication Deadline: {row.APPLICATION_DEADLINE}. " if pd.notna(row.APPLICATION_DEADLINE) and row.APPLICATION_DEADLINE != '' else '') + \
                       (f"\nCloses: {row.CLOSE_DATE}. " if pd.notna(row.CLOSE_DATE) and row.CLOSE_DATE != '' else '') + \
                       (f"\nTotal Funding: {row.TOTAL_FUNDING_AMOUNT}. " if pd.notna(row.TOTAL_FUNDING_AMOUNT) and row.TOTAL_FUNDING_AMOUNT != '' else '') + \
                       (f"\nAward Ceiling: {row.AWARD_CEILING}. " if pd.notna(row.AWARD_CEILING) and row.AWARD_CEILING != '' else '') + \
                       (f"\nAward Floor: {row.AWARD_FLOOR}. " if pd.notna(row.AWARD_FLOOR) and row.AWARD_FLOOR != '' else '') + \
                       (f"\nLink: {row.LINK}. " if pd.notna(row.LINK) and row.LINK != '' else '') + \
                       (f"\n{row.DESCRIPTION}" if pd.notna(row.DESCRIPTION) and row.DESCRIPTION != '' else '')
            }
            for i, row in enumerate(self.df.itertuples(index=False))
        ]
        self.formatted_data = data

    def format_tech_data(self):
        data = [
            {
                "id": f"vec{i}",
                "text": f"{row.title}. " + \
                       (f"\nUniversity: {row.university}. " if pd.notna(row.university) and row.university != '' else '') + \
                       (f"\nNumber: {row.number}. " if pd.notna(row.number) and row.number != '' else '') + \
                       (f"\nPatents: {row.patent}. " if pd.notna(row.patent) and row.patent != '' else '') + \
                       (f"\nLink: {row.link}. " if pd.notna(row.link) and row.link != '' else '') + \
                       (f"\n{row.description}" if pd.notna(row.description) and row.description != '' else '')
            }
            for i, row in enumerate(self.df.itertuples(index=False))
        ]
        self.formatted_data = data

    def generate_embeddings(self):
        print("Preparing data for embedding generation...")
        data = self.formatted_data

        print(f"Total items to process: {len(data)}")

        for i in range(self.batch_start*95, len(data), 95):
            print(f"Processing batch {i//95 + 1} of {len(data)//95 + 1}...")
            embeddings = self.pc.inference.embed(
                model='multilingual-e5-large',
                inputs=[d['text'] for d in data[i:i+95]],
                parameters={"input_type": "passage", "truncate": "END"}
            )

            print("Waiting for index to be ready...")
            while not self.pc.describe_index(self.index_name).status['ready']:
                time.sleep(1)
                print(".", end="", flush=True)
            print("\nIndex is ready.")

            index = self.pc.Index(self.index_name)

            print("Preparing vectors for upsert...")
            vectors = []
            for d, e in zip(data[i:i+95], embeddings):
                vectors.append({
                    "id": d['id'],
                    "values": e['values'],
                    "metadata": {'text': d['text']}
                })

            print(f"Upserting {len(vectors)} vectors...")
            index.upsert(
                vectors=vectors,
                namespace="ns1"
            )
            print("Upsert complete.")
            print("Waiting 5 seconds before next batch...")
            time.sleep(5)

        print("Embedding generation and upsert process complete.")

if __name__ == "__main__":

    option = 'tech' # 'grants' or 'tech', this is the only things that needs to be changed

    options = {
        'grants': {
            'index_name': 'grants-2024-11-21',
            'data_path': 'data/grants',
            'required_cols': ["OPPORTUNITY TITLE","AGENCY CODE","OPPORTUNITY STATUS",
                            "POSTED DATE","CLOSE DATE","LINK","OPPORTUNITY NUMBER",
                            "CATEGORY","LAST_UPDATED_DATE","POSTED_DATE","APPLICATION_DEADLINE",
                            "TOTAL_FUNDING_AMOUNT","AWARD_CEILING","AWARD_FLOOR","DESCRIPTION"],
            'format_data': 'format_grants_data'
        },
        'tech': {
            'index_name': 'tech-2024-11-21',
            'data_path': 'data/tech',
            'required_cols': ["university", "title", "number", "patent", "link", "description"],
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
    getattr(eg, options[option]['format_data'])()
    eg.generate_embeddings()
    print("Embedding generation process finished.")