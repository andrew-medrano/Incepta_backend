import argparse
from main import create_app
from main.services.search_service import SemanticSearch

if __name__ == '__main__':
    # Initialize SemanticSearch
    pinecone_api_key_path = "/Users/andre/startup/pinecone_api_key.txt"
    ss = SemanticSearch(
        pinecone_api_key_path=pinecone_api_key_path,
    )

    # Create Flask app
    app = create_app(ss)

    # Run the app
    app.run(debug=True)