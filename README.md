Incepta Backend
==============

A semantic search engine backend that enables intelligent searching across university technology databases and government grants using embeddings and LLM-powered explanations.

Features
--------
* Semantic Search: Advanced search capabilities using embeddings and cross-encoder reranking
* Dual Search Modes: 
  - Patents search (Stanford University Technology Database)
  - Grants search (SBIR Government Grants)
* Modern UI: Responsive web interface with gradient styling and intuitive search
* LLM-Powered: Intelligent search powered by embeddings and GPT-4 explanations
* Cross-Encoder Reranking: Enhanced result relevance using ms-marco-MiniLM-L-6-v2
* About Page: Team information and mission statement

Project Structure
---------------
Incepta_backend/
|-- README.md          # Project overview and setup instructions
|-- requirements.txt   # Python package dependencies
|-- main/
|   |-- static/
|   |   |-- images/   # Static assets (logo, team photos)
|   |       |-- logo.png
|   |       |-- NickMaynes.jpeg
|   |       |-- FerozeMohideen.jpeg
|   |-- templates/
|   |   |-- index_2.html     # Main search interface
|   |   |-- about.html       # About page
|   |-- embeddings_generator.py          # Generate embeddings for data
|   |-- semantic_search_app.py           # Flask application
|   |-- semantic_llm_search.py           # Search engine core
|-- data/
    |-- stanford_techfinder_133_pages.csv
    |-- grants_sbir_2000_pages.csv

Setup & Running
-------------
1. Install required packages:
   pip install flask sentence-transformers pinecone-client openai nltk asyncio

2. Set up your API keys:
   - Create a file for your Pinecone API key
   - Create a file for your OpenAI API key
   - Update the paths in semantic_search_app.py

3. Run the web application:
   cd Incepta_backend/main
   python semantic_search_app.py --pinecone_api_key_path /path/to/pinecone_key.txt --openai_api_key_path /path/to/openai_key.txt

4. Access the application:
   - Open your browser and navigate to http://localhost:5000
   - Use the search bar to query patents or grants
   - Toggle between Patents and Grants using the buttons
   - Visit the About page to learn more about Incepta

Technical Details
---------------
- Flask backend with async search capabilities
- Modern UI with gradient styling and responsive design
- Cross-encoder reranking for improved search relevance
- GPT-4 powered result explanations
- Pinecone vector database for efficient similarity search
- NLTK for text processing
- Sentence transformers for embedding generation

Data Sources
-----------
- Stanford TechFinder database (scraped on 11/17/2024)
- SBIR Government Grants database (downloaded from SBIR.gov on 11/17/2024)
- Embeddings stored in Pinecone indexes: stanford-techfinder-133-v1 and grants-sbir-2000-v1

Development Notes
---------------
- The application uses Flask for the backend server
- Frontend built with modern HTML5 and CSS3
- Search results returned via AJAX calls
- Async/await pattern for efficient search operations
- Cross-encoder reranking for better result quality