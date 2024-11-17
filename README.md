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
    - To run this script, you need to provide the path to the Pinecone API key file and the OpenAI API key file.
- `embeddings_search.py`: Basic embeddings-based vector search
    - To run this script, you need to provide the path to the Pinecone API key file.

### Data Processing
- `embeddings_generator.py`: Generates and stores embeddings in Pinecone
- `scrapers/base_scraper.py`: Base scraper class for other scrapers to inherit from
- `scrapers/stanford_scraper.py`: Web scraper for Stanford's TechFinder database

### Data Storage
- `/data/`: Directory for storing scraped data
    - `stanford_techfinder_133_pages.csv`: CSV file containing scraped data from Stanford's TechFinder database. Generated using `scrapers/stanford_scraper.py` on __11/17/2024__
    - `grants_sbir_2000_pages.csv`: CSV file containing scraped data from the SBIR Government Grants database. Downloaded from [SBIR.gov](https://www.sbir.gov/topics) on __11/17/2024__
- Pinecone vectors are stored in the `stanford-techfinder-133-v1` and `grants-sbir-2000-v1` indexes in the cloud. They are accessed using the `semantic_llm_search.py` and `embeddings_search.py` scripts with the appropriate API keys.