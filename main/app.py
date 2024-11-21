from flask import Flask, render_template, request, jsonify
from services.search_service import SemanticSearch
import argparse

app = Flask(__name__)

# Initialize semantic search
ss = None  # We'll initialize this in the main block

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query')
    index_name = request.json.get('index', 'stanford tech')
    
    # Update index if needed
    if index_name != ss.index_name:
        ss.set_index(index_name)
    
    # Use search_sync instead of search
    results = ss.search_sync(query)
    
    # Format results
    formatted_results = []
    for match in results:
        try:
            full_text = match['metadata']['text']
            title, *rest_of_text = full_text.split('. ', 1)
            display_text = (rest_of_text[0] if rest_of_text else '')
            
            # Ensure all values are JSON serializable
            formatted_result = {
                'score': float(match.get('relevance_score', 0)),  # Convert to float
                'title': str(title),  # Convert to string
                'text': str(display_text),  # Convert to string
                # 'explanation': str(match.get('explanation', ''))  # Convert to string, use empty string if missing
            }
            formatted_results.append(formatted_result)
        except Exception as e:
            print(f"Error processing match: {e}")
            print(f"Match data: {match}")
            continue
    
    return jsonify(formatted_results)

@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Web App for Semantic Search")
    parser.add_argument("--pinecone_api_key_path", type=str, 
                       help="Path to the Pinecone API key file", default="/Users/andre/startup/pinecone_api_key.txt")
    parser.add_argument("--openai_api_key_path", type=str,
                       help="Path to the OpenAI API key file", default="/Users/andre/startup/openai_api_key.txt")
    args = parser.parse_args()

    ss = SemanticSearch(pinecone_api_key_path=args.pinecone_api_key_path,
                       openai_api_key_path=args.openai_api_key_path)
    app.run(debug=True)
