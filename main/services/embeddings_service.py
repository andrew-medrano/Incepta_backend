import pandas as pd
from pinecone import Pinecone, ServerlessSpec
import time
import os

class EmbeddingsGenerator:
    def __init__(self, data_path, index_name = "stanford-techfinder-10-v2", batch_start = 0):
        self.pc = None
        self.index_name = index_name
        self.data_path = data_path
        self.batch_start = batch_start

    def setup(self):
        print("Setting up Pinecone client...")
        PINECONE_API_KEY = open("/Users/andre/startup/pinecone_api_key.txt", "r").read()
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        print("Pinecone client setup complete.")

    

    def load_data(self):
        print("Loading data from CSV...")
        for file in os.listdir(self.data_path):
            if file.endswith('.csv'):
                df = pd.read_csv(os.path.join(self.data_path, file))
                # Verify required columns exist
                required_cols = ["OPPORTUNITY TITLE","AGENCY CODE","OPPORTUNITY STATUS",
                                 "POSTED DATE","CLOSE DATE","LINK","OPPORTUNITY NUMBER",
                                 "CATEGORY","LAST_UPDATED_DATE","POSTED_DATE","APPLICATION_DEADLINE",
                                 "TOTAL_FUNDING_AMOUNT","AWARD_CEILING","AWARD_FLOOR","DESCRIPTION"]

                if not all(col in df.columns for col in required_cols):
                    print(f"Warning: {file} missing required columns {required_cols}")
                    continue
                
                # Initialize self.df if not already set
                if not hasattr(self, 'df'):
                    self.df = df
                else:
                    # Append only if columns match
                    if set(df.columns) == set(self.df.columns):
                        self.df = pd.concat([self.df, df], ignore_index=True)
                    else:
                        print(f"Warning: {file} columns do not match existing dataframe")
                        continue
                
                print(f"{file} loaded. Total rows now: {len(self.df)}")

        # Clean column names
        self.df.columns = self.df.columns.str.replace(' ', '_')
        print("Column names cleaned.")

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

    def format_data(self):
        data = [
            {
                "id": f"vec{i}",
                "text": f"{row.OPPORTUNITY_TITLE}. " + \
                       (f"Number: {row.OPPORTUNITY_NUMBER}. " if pd.notna(row.OPPORTUNITY_NUMBER) and row.OPPORTUNITY_NUMBER != '' else '') + \
                       (f"Agency: {row.AGENCY_CODE}. " if pd.notna(row.AGENCY_CODE) and row.AGENCY_CODE != '' else '') + \
                       (f"Category: {row.CATEGORY}. " if pd.notna(row.CATEGORY) and row.CATEGORY != '' else '') + \
                       (f"Status: {row.OPPORTUNITY_STATUS}. " if pd.notna(row.OPPORTUNITY_STATUS) and row.OPPORTUNITY_STATUS != '' else '') + \
                       (f"Posted: {row.POSTED_DATE}. " if pd.notna(row.POSTED_DATE) and row.POSTED_DATE != '' else '') + \
                       (f"Last Updated: {row.LAST_UPDATED_DATE}. " if pd.notna(row.LAST_UPDATED_DATE) and row.LAST_UPDATED_DATE != '' else '') + \
                       (f"Application Deadline: {row.APPLICATION_DEADLINE}. " if pd.notna(row.APPLICATION_DEADLINE) and row.APPLICATION_DEADLINE != '' else '') + \
                       (f"Closes: {row.CLOSE_DATE}. " if pd.notna(row.CLOSE_DATE) and row.CLOSE_DATE != '' else '') + \
                       (f"Total Funding: {row.TOTAL_FUNDING_AMOUNT}. " if pd.notna(row.TOTAL_FUNDING_AMOUNT) and row.TOTAL_FUNDING_AMOUNT != '' else '') + \
                       (f"Award Ceiling: {row.AWARD_CEILING}. " if pd.notna(row.AWARD_CEILING) and row.AWARD_CEILING != '' else '') + \
                       (f"Award Floor: {row.AWARD_FLOOR}. " if pd.notna(row.AWARD_FLOOR) and row.AWARD_FLOOR != '' else '') + \
                       (f"Link: {row.LINK}. " if pd.notna(row.LINK) and row.LINK != '' else '') + \
                       (f"{row.DESCRIPTION}" if pd.notna(row.DESCRIPTION) and row.DESCRIPTION != '' else '')
            }
            for i, row in enumerate(self.df.itertuples(index=False))
        ]
        return data

    def generate_embeddings(self):
        print("Preparing data for embedding generation...")
        data = self.format_data()

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
    index_name = 'grants-2024-11-21'
    data_path = 'data/grants'

    eg = EmbeddingsGenerator(
        index_name=index_name,
        data_path=data_path,
    )

    print("Starting embedding generation process...")
    eg.setup()
    eg.load_data()
    eg.create_index()
    eg.generate_embeddings()
    print("Embedding generation process finished.")