# Incepta Backend

A semantic search engine backend that enables intelligent searching across university technology databases and government grants using embeddings and LLM-powered explanations.

## Features

- **Semantic Search**: Advanced search capabilities using embeddings and cross-encoder reranking
- **Dual Search Modes**: 
  - Patents search (Stanford University Technology Database)
  - Grants search (SBIR Government Grants)
- **Web Interface**: Modern, responsive web interface for easy searching
- **LLM-Powered**: Intelligent search powered by embeddings and language models

## Project Structure

Incepta_backend/
├── README.md          # Project overview and setup instructions
├── requirements.txt   # Python package dependencies
├── main/
│   ├── static/
│   │   └── images/        # Static assets
│   ├── templates/
│   │   └── index.html     # Web interface
│   ├── embeddings_generator.py          # Generate embeddings for data
│   ├── embeddings_search_app.py         # Flask application
│   ├── embeddings_search.py             # Embeddings search
│   └── semantic_llm_search.py           # LLM-enhanced embeddings search
├── data/
│   ├── stanford_techfinder_133_pages.csv
│   └── grants_sbir_2000_pages.csv

## Setup & Running

1. Install required packages:
pip install flask beautifulsoup4 pinecone-client openai

2. Set up your API keys:
- Create a file for your Pinecone API key
- Create a file for your OpenAI API key
- Update the paths in web_app.py

3. Run the web application:
cd Incepta_backend/main
python web_app.py

4. Access the application:
- Open your browser and navigate to http://localhost:5000
- Use the search bar to query patents or grants
- Toggle between Patents and Grants using the buttons

## Data Sources

- Stanford TechFinder database (scraped on 11/17/2024)
- SBIR Government Grants database (downloaded from SBIR.gov on 11/17/2024)
- Embeddings stored in Pinecone indexes: stanford-techfinder-133-v1 and grants-sbir-2000-v1

## Development Notes

- The application uses Flask for the backend server
- Frontend built with HTML, CSS, and jQuery
- Search results are returned via AJAX calls
- Embeddings and semantic search handled by separate modules