import os
# Set this before importing any HuggingFace libraries
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from pinecone import Pinecone
from sentence_transformers import CrossEncoder, SentenceTransformer
import numpy as np
from nltk.tokenize import sent_tokenize
import nltk
from openai import AsyncOpenAI
import os
import tkinter as tk
from tkinter import ttk, scrolledtext
import argparse
import asyncio

# Download NLTK data files (only need to run once)
nltk.download('punkt')

class SemanticSearch:
    def __init__(self, index_name="stanford tech", top_k=10, pinecone_api_key_path=None, openai_api_key_path=None):
        self.index_aliases = {
            "stanford tech": "stanford-techfinder-133-v1",
            "grants sbir": "grants-sbir-2000-v1"
        }
        PINECONE_API_KEY = open(pinecone_api_key_path, "r").read().strip() if pinecone_api_key_path else os.getenv('PINECONE_API_KEY')
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.set_index(index_name)
        self.top_k = top_k
        # Load the cross-encoder model for re-ranking
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        # Load the sentence embedding model for explanation generation
        self.sentence_embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Add OpenAI client initialization
        self.MODEL = "gpt-4o-mini"
        OPENAI_API_KEY = open(openai_api_key_path, "r").read().strip() if openai_api_key_path else os.getenv('OPENAI_API_KEY')
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)

    def set_index(self, index_name):
        actual_index_name = self.index_aliases.get(index_name, index_name)
        self.index = self.pc.Index(actual_index_name)
        self.index_name = index_name

    async def search(self, query):
        # Perform initial retrieval using embeddings
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
            top_k=self.top_k * 5,  # Retrieve more candidates for re-ranking
            include_values=False,
            include_metadata=True
        )
        # Extract documents from the results
        documents = [match['metadata']['text'] for match in results['matches']]
        # Pair the query with each document for re-ranking
        pairs = [[query, doc] for doc in documents]
        # Compute relevance scores using the cross-encoder
        scores = self.cross_encoder.predict(pairs)
        # Attach scores to matches
        for idx, match in enumerate(results['matches']):
            match['relevance_score'] = scores[idx]
        # Sort matches based on the relevance scores
        sorted_matches = sorted(results['matches'], key=lambda x: x['relevance_score'], reverse=True)
        # Select top_k results
        top_matches = sorted_matches[:self.top_k]
        # Generate explanations in parallel
        explanation_tasks = []
        for match in top_matches:
            document_text = match['metadata']['text']
            task = self.generate_explanation(query, document_text)
            explanation_tasks.append(task)
        
        # Wait for all explanations to complete
        explanations = await asyncio.gather(*explanation_tasks)
        
        # Attach explanations to matches
        for match, explanation in zip(top_matches, explanations):
            match['explanation'] = explanation
            
        return top_matches

    async def generate_explanation(self, query, document_text):
        # Create a prompt for the LLM
        prompt = f"""Given the search query: "{query}"
        And this document excerpt: "{document_text}"
        
        Provide a brief (1-2 sentences) explanation of why this document is relevant to the query.
        Focus on the specific aspects that make it a good match."""

        response = await self.client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that very briefly explains document relevance. Be concise and don't explain anything that is redundant or obvious. Start with 'This document discusses', and jump directly into explanation."},
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.choices[0].message.content.strip()

    def search_sync(self, query):
        """Synchronous wrapper for the async search method"""
        return asyncio.run(self.search(query))

class SearchGUI:
    def __init__(self, master, ss: SemanticSearch, title="Semantic Search on University Tech and Government Grants", geometry="800x1000", index_name="stanford tech"):
        self.master = master
        self.master.title(title)
        self.master.geometry(geometry)

        self.ss = ss
        self.create_widgets()

    def create_widgets(self):
        # Index selection
        ttk.Label(self.master, text="Select index:").pack(pady=5)
        self.index_combobox = ttk.Combobox(self.master, values=["stanford tech", "grants sbir"], width=47)
        self.index_combobox.set(self.ss.index_name)
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
        self.ss.set_index(new_index)

    def perform_search(self):
        query = self.query_entry.get()
        # Run the async search in the event loop
        results = asyncio.run(self.ss.search(query))
        
        self.results_text.delete(1.0, tk.END)
        for match in results:
            score = match['relevance_score']
            full_text = match['metadata']['text']#.replace('\n', ' ')  # Remove newlines from full text
            title = full_text.split('.')[0]
            explanation = match['explanation']
            
            display_text = full_text[len(title):].replace('\n', ' ').strip()
            
            # Insert formatted text with explanation first
            self.results_text.insert(tk.END, f"Relevance Score: {score:.4f}\n", 'score')
            self.results_text.insert(tk.END, f"Title: {title}\n", 'title')
            self.results_text.insert(tk.END, f"Explanation: {explanation}\n", 'explanation')
            self.results_text.insert(tk.END, f"Text: {display_text}\n\n", 'text')

        # Add tags for styling with much larger fonts
        self.results_text.tag_configure('score', foreground='blue', font=('Helvetica', 16, 'bold'), 
                                      background='#f0f0f0')  # Light gray
        self.results_text.tag_configure('title', foreground='black', font=('Helvetica', 20, 'bold'), 
                                      background='#e6e6e6')  # Slightly darker gray
        self.results_text.tag_configure('text', foreground='black', font=('Helvetica', 16), 
                                      background='#ffffff')   # White
        self.results_text.tag_configure('explanation', foreground='green', font=('Helvetica', 16, 'italic'), 
                                      background='#f5f5f5')  # Very light gray

# Update the main block
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Semantic Search GUI")
    parser.add_argument("--index", type=str, default="stanford tech", help="Name of the Pinecone index to use")
    parser.add_argument("--title", type=str, default="Semantic Search on University Tech and Government Grants", help="Title for the GUI window")
    parser.add_argument("--geometry", type=str, default="800x1000", help="Geometry of the GUI window")
    args = parser.parse_args()

    pinecone_api_key_path = input("Enter the path to the Pinecone API key file: ") or "/Users/andre/startup/pinecone_api_key.txt"
    openai_api_key_path = input("Enter the path to the OpenAI API key file: ") or "/Users/andre/startup/openai_api_key.txt"
    if not pinecone_api_key_path or not openai_api_key_path:
        print("Error: Pinecone and OpenAI API key paths are required.")
        parser.print_help()
        exit(1)

    root = tk.Tk()
    ss = SemanticSearch(index_name=args.index, pinecone_api_key_path=pinecone_api_key_path, openai_api_key_path=openai_api_key_path)
    app = SearchGUI(root, ss, title=args.title, geometry=args.geometry, index_name=args.index)
    root.mainloop()
