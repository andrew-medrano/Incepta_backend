from flask import Blueprint, request, jsonify, current_app

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['POST'])
def search():
    query = request.json.get('query')
    index_name = request.json.get('index', 'stanford tech')

    # Access SemanticSearch from the app's config
    ss = current_app.config['SEMANTIC_SEARCH']

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
            }
            formatted_results.append(formatted_result)
        except Exception as e:
            print(f"Error processing match: {e}")
            print(f"Match data: {match}")
            continue

    return jsonify(formatted_results)