Incepta Backend
==============

A semantic search engine backend that enables intelligent searching across university technology databases and government grants using embeddings and LLM-powered explanations.

Features
--------
* Semantic Search: Advanced search capabilities using embeddings and cross-encoder reranking
* Dual Search Modes: 
  - Patents search (Stanford University Technology Database)
  - Grants search (Grants.gov and DOD SBIR/STTR)
* Modern UI: Responsive web interface with gradient styling and intuitive search
* LLM-Powered: Intelligent search powered by embeddings and GPT-4 explanations
* Cross-Encoder Reranking: Enhanced result relevance using ms-marco-MiniLM-L-6-v2
* About Page: Team information and mission statement

Project Structure
---------------
Incepta_backend/
|-- README.md                 # Project overview and setup instructions
|-- requirements.txt          # Python package dependencies
|-- .env                      # Environment variables for API keys (TO BE ADDED)
|-- config.py                 # Centralized configuration file (TO BE ADDED)

|-- data/
|   |-- grants/               # All grants-related data
|   |   |-- unprocessed/      
|   |   |   |-- grants_dodsbirstr.py       
|   |   |-- grants_gov_scraped_2024_11_20.csv
|   |   |-- dodsbirstr_2024_11_21.csv
|   |-- tech/                 # All tech-related data
|   |   |-- stanford_2024_11_18.csv

|-- main/                     # Main application logic
|   |-- __init__.py           # Initializes app as a package
|   |-- app.py                # Entry point for Flask app (move semantic_search_app.py here)
|   |-- blueprints/           # Folder for modular routes
|   |   |-- __init__.py
|   |   |-- search.py         # Search routes
|   |   |-- about.py          # About page routes
|   |-- services/             # Business logic and core services
|   |   |-- __init__.py
|   |   |-- embeddings_service.py  # Embedding-related utilities (move embeddings_generator.py here)
|   |   |-- search_service.py      # Search logic (move semantic_llm_search.py here)
|   |-- static/               # Static assets (CSS, JS, images)
|   |   |-- images/           # Images
|   |   |   |-- FerozeMohideen.jpeg
|   |   |   |-- logo.png
|   |   |   |-- NickMaynes.jpeg
|   |-- templates/            # HTML templates
|       |-- index.html        # Main search interface (rename index_2.html)
|       |-- about.html        # About page

|-- scrapers/                 # Scraping scripts
|   |-- scraper_spec.pdf      # Scraping specification
|   |-- grants/
|   |   |-- grants_dodsbirstr.py
|   |   |-- grants_gov.py
|   |-- tech/
|       |-- __init__.py
|   |   |-- base_scraper.py       # Base scraper template
|   |   |-- blank_scraper_template.py
|   |   |-- stanford_scraper.py

Not implemented yet:
|-- tests/                    # Testing folder
|   |-- __init__.py
|   |-- test_app.py           # App-level tests
|   |-- test_services.py      # Service-level tests
|   |-- test_scrapers.py      # Scraper tests

|-- deployment/               # Deployment-related configurations
|   |-- Dockerfile            # Docker configuration (to be added)
|   |-- docker-compose.yml    # Optional: Multi-container setup (to be added)
|   |-- gunicorn_config.py    # Gunicorn config (to be added)
|   |-- nginx/                # NGINX configuration
|       |-- nginx.conf


Setup & Running
-------------
1. Install required packages:
   - look at requirements.txt

2. Set up your API keys:
   - Create a file for your Pinecone API key
   - Create a file for your OpenAI API key
   - Update the paths in search_service.py

3. Run the web application:
   cd Incepta_backend/main
   python app.py

4. Access the application:
   - Open your browser and navigate to the URL displayed in the terminal
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
- Grants.gov database (downloaded on 11/21/2024)
- DOD SBIR/STTR database (scraped on 11/21/2024)
- Embeddings stored in Pinecone indexes: stanford-techfinder-133-v1 and grants-2024-11-21

Development Notes
---------------
- The application uses Flask for the backend server
- Frontend built with modern HTML5 and CSS3
- Search results returned via AJAX calls
- Async/await pattern for efficient search operations
- Cross-encoder reranking for better result quality