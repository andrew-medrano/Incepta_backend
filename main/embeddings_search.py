from pinecone import Pinecone
import tkinter as tk
from tkinter import ttk, scrolledtext
import argparse
import os

class EmbeddingsSearch:
    def __init__(self, index_name="stanford tech", top_k=10, pinecone_api_key_path=None):
        self.index_aliases = {
            "stanford tech": "stanford-techfinder-133-v1",
            "grants sbir": "grants-sbir-2000-v1"
        }
        PINECONE_API_KEY = open(pinecone_api_key_path, "r").read().strip() if pinecone_api_key_path else os.getenv('PINECONE_API_KEY')
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.set_index(index_name)
        self.top_k = top_k
    def set_index(self, index_name):
        actual_index_name = self.index_aliases.get(index_name, index_name)
        self.index = self.pc.Index(actual_index_name)
        self.index_name = index_name

    def search(self, query):
        embedding = self.pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[query],
            parameters={
                "input_type": "query"
            }
        )

        results = self.index.query(
            namespace="ns1",
            vector=embedding[0].values,
            top_k=self.top_k,
            include_values=False,
            include_metadata=True
        )

        return results

class SearchGUI:
    def __init__(self, master, ss: EmbeddingsSearch, title="Embeddings Search on University Tech and Government Grants", geometry="600x800", index_name="stanford tech"):
        self.master = master
        self.master.title(title)
        self.master.geometry(geometry)

        self.es = ss

        self.create_widgets()

    def create_widgets(self):
        # Index selection
        ttk.Label(self.master, text="Select index:").pack(pady=5)
        self.index_combobox = ttk.Combobox(self.master, values=["stanford tech", "grants sbir"], width=47)
        self.index_combobox.set(self.es.index_name)
        self.index_combobox.pack()
        ttk.Button(self.master, text="Set Index", command=self.set_index).pack(pady=5)

        # Query input
        ttk.Label(self.master, text="Enter your query:").pack(pady=5)
        self.query_entry = ttk.Entry(self.master, width=50)
        self.query_entry.pack()

        # Search button
        ttk.Button(self.master, text="Search", command=self.perform_search).pack(pady=10)

        # Results display
        self.results_text = scrolledtext.ScrolledText(self.master, wrap=tk.WORD, width=100, height=300)
        self.results_text.pack(pady=10)

    def set_index(self):
        new_index = self.index_combobox.get()
        self.es.set_index(new_index)

    def perform_search(self):
        query = self.query_entry.get()
        results = self.es.search(query)
        
        self.results_text.delete(1.0, tk.END)
        for match in results['matches']:
            score = match['score']
            full_text = match['metadata']['text']
            title, *rest_of_text = full_text.split('. ', 1)
            
            # Limit text to 300 characters
            display_text = (rest_of_text[0] if rest_of_text else '')[:300] + '...'
            
            # Insert formatted text
            self.results_text.insert(tk.END, f"Score: {score:.2f}\n", 'score')
            self.results_text.insert(tk.END, f"Title: {title}\n", 'title')
            self.results_text.insert(tk.END, f"Text: {display_text}\n\n", 'text')

        # Add tags for styling
        self.results_text.tag_configure('score', foreground='blue', font=('Helvetica', 10, 'bold'), background='white')
        self.results_text.tag_configure('title', foreground='black', font=('Helvetica', 12, 'bold'), background='white') 
        self.results_text.tag_configure('text', foreground='black', font=('Helvetica', 10), background='white')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Embeddings Search GUI")
    parser.add_argument("--index", type=str, default="stanford tech", help="Name of the Pinecone index to use")
    parser.add_argument("--title", type=str, default="Embeddings Search on University Tech and Government Grants", help="Title for the GUI window")
    parser.add_argument("--geometry", type=str, default="600x800", help="Geometry of the GUI window")
    args = parser.parse_args()

    pinecone_api_key_path = input("Enter the path to the Pinecone API key file: ") or "/Users/andre/startup/pinecone_api_key.txt"

    root = tk.Tk()
    ss = EmbeddingsSearch(index_name=args.index, pinecone_api_key_path=args.pinecone_api_key_path)
    app = SearchGUI(root, ss, title=args.title, geometry=args.geometry, index_name=args.index)
    root.mainloop()