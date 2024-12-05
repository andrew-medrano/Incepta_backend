import os
# Set this before importing any HuggingFace libraries
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from pinecone import Pinecone
# from sentence_transformers import CrossEncoder, SentenceTransformer
import numpy as np
import os
import asyncio
from dotenv import load_dotenv
from main.constants.pinecone_indexes import INDEX_ALIASES
from main.constants.results_blacklist import GRANTS_BLACKLIST, TECH_BLACKLIST
class SemanticSearch:
    def __init__(self, index_name='tech', top_k=20):
        # Load environment variables
        load_dotenv()
        self.pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))

        self.index_aliases = INDEX_ALIASES
        self.index_name = index_name
        self.index = self.set_index(index_name)  # This line is fixed
        
        self.top_k = top_k

    def set_index(self, index_name):
        self.index_name = index_name
        actual_index_name = self.index_aliases.get(index_name, index_name)
        self.index = self.pc.Index(actual_index_name)
        return self.index

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
            top_k=self.top_k,  # Changed from self.top_k * 5 to just self.top_k
            include_values=False, 
            include_metadata=True, 
            filter=filter_dict if filter_dict else None
        )

        # Extract documents and add IDs to matches
        for match in results['matches']:
            match['id'] = match['id']
            match['metadata'] = match['metadata']
            match['relevance_score'] = match['score']  # Use the original similarity score

        # Filter out blacklisted results - fixing the blacklist check
        if self.index_name == 'grants':
            results['matches'] = [
                match for match in results['matches'] 
                if str(match['id']).strip().lower() not in {str(id).strip().lower() for id in GRANTS_BLACKLIST}
            ]
        elif self.index_name == 'tech':
            results['matches'] = [
                match for match in results['matches'] 
                if str(match['id']).strip().lower() not in {str(id).strip().lower() for id in TECH_BLACKLIST}
            ]
        
        return results['matches']

    def search_sync(self, query, category_filter=None):
        """Synchronous wrapper for the async search method"""
        return asyncio.run(self.search(query, category_filter=category_filter))

    def get_by_id(self, id):
        """Fetch a specific document by its ID"""
        try:
            response = self.index.fetch(ids=[id], namespace="ns1")
            if not response or not response.get('vectors'):
                return None
            
            vector_data = response['vectors'][id]
            return {
                'id': id,
                'metadata': vector_data.metadata,
                'score': 1.0  # Default score for direct fetches
            }
        except Exception as e:
            print(f"Error fetching document: {e}")
            return None

if __name__ == "__main__":
    ss = SemanticSearch(index_name="tech", pinecone_api_key_path="/Users/andre/startup/pinecone_api_key.txt")
    print(ss.search_sync("I want to solve climate change..."))