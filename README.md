# Incepta Backend

A semantic search engine backend that enables intelligent searching across university technology databases and government grants using embeddings and LLM-powered explanations.

## Features

- **Semantic Search**: Advanced search capabilities using embeddings and cross-encoder reranking
- **Dual Search Modes**: 
  - Simple embeddings-based search
  - Enhanced semantic search with LLM-powered explanations
- **Multiple Data Sources**:
  - Stanford University Technology Database
  - SBIR Government Grants
- **GUI Interface**: User-friendly interface for both search modes

## Components

### Search Engines
- `semantic_llm_search.py`: Advanced search with cross-encoder reranking and LLM explanations
- `embeddings_search.py`: Basic embeddings-based vector search

### Data Processing
- `embeddings_generator.py`: Generates and stores embeddings in Pinecone
- `scrapers/stanford_scraper.py`: Web scraper for Stanford's TechFinder database