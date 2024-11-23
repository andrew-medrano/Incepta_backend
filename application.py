import os
from dotenv import load_dotenv
from main import create_app
from main.services.search_service import SemanticSearch

# Load environment variables
load_dotenv()

# Initialize SemanticSearch with default index
ss = SemanticSearch(index_name='tech')
application = create_app(ss)

# This will only run in development
if __name__ == '__main__':
    if os.getenv('FLASK_ENV') == 'development':
        application.run(
            debug=True,
            host=os.getenv('FLASK_HOST', '127.0.0.1'),
            port=int(os.getenv('FLASK_PORT', 5001))
        )
    else:
        # In production, Gunicorn will import 'application'
        # This block won't run
        print("Please use gunicorn for production deployment")