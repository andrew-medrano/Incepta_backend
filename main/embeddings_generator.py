import pandas as pd
from pinecone import Pinecone, ServerlessSpec
import time

class EmbeddingsGenerator:
    def __init__(self, data_path, index_name = "stanford-techfinder-10-v2", batch_start = 0, data_limit = 2000):
        self.pc = None
        self.index_name = index_name
        self.data_path = data_path
        self.batch_start = batch_start
        self.data_limit = data_limit

    def setup(self):
        print("Setting up Pinecone client...")
        PINECONE_API_KEY = open("/Users/andre/startup/pinecone_api_key.txt", "r").read()
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        print("Pinecone client setup complete.")

    def load_data(self):
        print("Loading data from CSV...")
        self.df = pd.read_csv(self.data_path).head(self.data_limit)
        print(f"Data loaded. {len(self.df)} rows found.")

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
                "text": f"{row.title}. {row.description}"
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
            print("Waiting 10 seconds before next batch...")
            time.sleep(5)

        print("Embedding generation and upsert process complete.")

if __name__ == "__main__":
    index_name = input("Enter the name of the Pinecone index to use (default: grants-sbir-2000-v1): ") or "grants-sbir-2000-v1"
    data_path = input("Enter the path to the CSV file containing the data: ") or "/Users/andre/startup/Incepta_backend/data/grants/topics_search_1731781387.csv"

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