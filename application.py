import os
from dotenv import load_dotenv
from main import create_app
from main.services.search_service import SemanticSearch

# Load environment variables
load_dotenv()

# Initialize SemanticSearch with default index
ss = SemanticSearch(index_name='tech')
application = create_app(ss)

# Get port from environment variable or use default
port = os.getenv('PORT')
if port is None or port == "":
    port = 5001
else:
    port = int(port)

# This will only run in development
if __name__ == '__main__':
    application.run(
        debug=os.getenv('FLASK_ENV') == 'development',
        host='0.0.0.0',  # Listen on all available interfaces
        port=port
    )

@application.route('/health')
def health():
    return 'OK', 200
