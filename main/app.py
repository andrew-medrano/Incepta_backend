import os
from dotenv import load_dotenv
from main import create_app
from main.services.search_service import SemanticSearch

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    # Initialize SemanticSearch with default index
    ss = SemanticSearch(index_name='tech')  # Set a default index

    # Create Flask app
    app = create_app(ss)

    # Run the app
    app.run(
        host=os.getenv('FLASK_HOST', '127.0.0.1'),
        port=int(os.getenv('FLASK_PORT', 5001))
    )