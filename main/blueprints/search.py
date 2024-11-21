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
            full_text = match['metadata']['text'].replace('\\n', '<br>')
            
            # Split on first period to get title
            title, *rest_of_text = full_text.split('. ', 1)
            
            # Initialize common fields
            formatted_result = {
                'score': float(match.get('relevance_score', 0)),
                'title': str(title),
                'text': '',
                'metadata': {}
            }
            
            # Extract metadata based on index type
            if index_name == 'stanford tech':
                # Parse tech transfer data
                text_parts = rest_of_text[0].split('\n') if rest_of_text else []
                for part in text_parts:
                    if part.startswith('University: '):
                        formatted_result['metadata']['university'] = part.replace('University: ', '').rstrip('.')
                    elif part.startswith('Number: '):
                        formatted_result['metadata']['number'] = part.replace('Number: ', '').rstrip('.')
                    elif part.startswith('Patents: '):
                        formatted_result['metadata']['patents'] = part.replace('Patents: ', '').rstrip('.')
                    elif part.startswith('Link: '):
                        formatted_result['metadata']['link'] = part.replace('Link: ', '').rstrip('.')
                    else:
                        formatted_result['text'] = formatted_result['text'] + part  # This should be the description
                        
            else:  # grants data
                text_parts = rest_of_text[0].split('\n') if rest_of_text else []
                for part in text_parts:
                    if part.startswith('Number: '):
                        formatted_result['metadata']['number'] = part.replace('Number: ', '').rstrip('.')
                    elif part.startswith('Agency: '):
                        formatted_result['metadata']['agency'] = part.replace('Agency: ', '').rstrip('.')
                    elif part.startswith('Category: '):
                        formatted_result['metadata']['category'] = part.replace('Category: ', '').rstrip('.')
                    elif part.startswith('Status: '):
                        formatted_result['metadata']['status'] = part.replace('Status: ', '').rstrip('.')
                    elif part.startswith('Posted: '):
                        formatted_result['metadata']['posted_date'] = part.replace('Posted: ', '').rstrip('.')
                    elif part.startswith('Application Deadline: '):
                        formatted_result['metadata']['deadline'] = part.replace('Application Deadline: ', '').rstrip('.')
                    elif part.startswith('Total Funding: '):
                        formatted_result['metadata']['total_funding'] = part.replace('Total Funding: ', '').rstrip('.')
                    elif part.startswith('Link: '):
                        formatted_result['metadata']['link'] = part.replace('Link: ', '').rstrip('.')
                    elif not part.startswith(('Last Updated:', 'Closes:', 'Award Ceiling:', 'Award Floor:')):
                        formatted_result['text'] = formatted_result['text'] + part  # This should be the description

            formatted_results.append(formatted_result)
        except Exception as e:
            print(f"Error processing match: {e}")
            print(f"Match data: {match}")
            continue

    return jsonify(formatted_results)