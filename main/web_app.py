from flask import Flask, render_template, request, jsonify
from embeddings_search import EmbeddingsSearch
import argparse

app = Flask(__name__)

# Initialize your embeddings search
es = None  # We'll initialize this in the main block

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query')
    index_name = request.json.get('index', 'stanford tech')
    
    # Update index if needed
    if index_name != es.index_name:
        es.set_index(index_name)
    
    # Perform search
    results = es.search(query)
    
    # Format results
    formatted_results = []
    for match in results['matches']:
        full_text = match['metadata']['text']
        title, *rest_of_text = full_text.split('. ', 1)
        display_text = (rest_of_text[0] if rest_of_text else '')[:300] + '...'
        
        formatted_results.append({
            'score': round(match['score'], 2),
            'title': title,
            'text': display_text
        })
    
    return jsonify(formatted_results)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Web App for Embeddings Search")
    parser.add_argument("--pinecone_api_key_path", type=str, required=True, help="Path to the Pinecone API key file", default="/Users/andre/startup/pinecone_api_key.txt")
    args = parser.parse_args()

    es = EmbeddingsSearch(pinecone_api_key_path=args.pinecone_api_key_path)
    app.run(debug=True)