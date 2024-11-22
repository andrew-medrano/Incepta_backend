import os
# Set this before importing any HuggingFace libraries
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from pinecone import Pinecone
from sentence_transformers import CrossEncoder, SentenceTransformer
import numpy as np
from nltk.tokenize import sent_tokenize
import nltk
import os
import asyncio

# Download NLTK data files (only need to run once)
nltk.download('punkt')

class SemanticSearch:
    def __init__(self, index_name="tech", top_k=20, pinecone_api_key_path=None):
        self.index_aliases = {
            "tech": "tech-2024-11-21",
            "grants": "grants-2024-11-21"
        }
        PINECONE_API_KEY = open(pinecone_api_key_path, "r").read().strip() if pinecone_api_key_path else os.getenv('PINECONE_API_KEY')
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.set_index(index_name)
        self.top_k = top_k
        # Load the cross-encoder model for re-ranking
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        # Load the sentence embedding model for explanation generation
        self.sentence_embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def set_index(self, index_name):
        actual_index_name = self.index_aliases.get(index_name, index_name)
        self.index = self.pc.Index(actual_index_name)
        self.index_name = index_name

    async def search(self, query, category_filter=None):
        """
        could add filter for:
        - university
        - agency code
        """
        # Perform initial retrieval using embeddings
        embedding = self.pc.inference.embed(
            model="multilingual-e5-large",
            inputs=[query],
            parameters={"input_type": "query"}
        )

        # Add filter if category is specified
        filter_dict = {}
        if category_filter:
            # Handle both single category and list of categories
            categories = [category_filter] if isinstance(category_filter, str) else category_filter
            filter_dict = {
                "$or": [
                    {"category": {"$in": categories}},
                ]
            }

        results = self.index.query(
            namespace="ns1",
            vector=embedding[0].values,
            top_k=self.top_k * 5,  # Retrieve more candidates for re-ranking
            include_values=False, 
            include_metadata=True, 
            filter=filter_dict if filter_dict else None
        )

        # Extract documents using 'description' field instead of 'text'
        documents = [match['metadata']['description'] for match in results['matches']]
        
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
            
        return top_matches

    def search_sync(self, query, category_filter=None):
        """Synchronous wrapper for the async search method"""
        return asyncio.run(self.search(query, category_filter=category_filter))


if __name__ == "__main__":
    ss = SemanticSearch(index_name="tech", pinecone_api_key_path="/Users/andre/startup/pinecone_api_key.txt")
    print(ss.search_sync("I want to solve climate change..."))