import argparse
from main import create_app
from main.services.search_service import SemanticSearch

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Web App for Tech and Grants Search")
    parser.add_argument("--pinecone_api_key_path", type=str,
                        help="Path to the Pinecone API key file", default="/Users/andre/startup/pinecone_api_key.txt")
    parser.add_argument("--openai_api_key_path", type=str,
                        help="Path to the OpenAI API key file", default="/Users/andre/startup/openai_api_key.txt")
    args = parser.parse_args()

    # Initialize SemanticSearch
    ss = SemanticSearch(
        pinecone_api_key_path=args.pinecone_api_key_path,
        openai_api_key_path=args.openai_api_key_path
    )

    # Create Flask app
    app = create_app(ss)

    # Run the app
    app.run(debug=True)