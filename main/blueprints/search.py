from flask import Blueprint, request, jsonify, current_app
from main.services.search_service import SemanticSearch

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['POST'])
def search():
    query = request.json.get('query')
    index_name = request.json.get('index', 'tech')
    category_filter = request.json.get('categories')

    ss = current_app.config['SEMANTIC_SEARCH']
    if index_name != ss.index_name:
        ss.set_index(index_name)

    results = ss.search_sync(query, category_filter=category_filter)

    formatted_results = []
    for match in results:
        try:
            metadata = match['metadata']
            formatted_result = {
                'score': float(match.get('relevance_score', 0)),
                'title': metadata.get('title', ''),
                'description': metadata.get('description', '').replace('\\n', '<br>').encode('ascii', 'ignore').decode(),
                'metadata': {}
            }
            
            if index_name == 'tech':
                formatted_result['metadata'].update({
                    'university': metadata.get('university', ''),
                    'number': metadata.get('number', ''),
                    'patent': metadata.get('patent', ''),
                    'link': metadata.get('link', ''),
                    'category': metadata.get('category', [])
                })
            else:
                formatted_result['metadata'].update({
                    'opportunity_number': metadata.get('opportunity_number', ''),
                    'agency_code': metadata.get('agency_code', ''),
                    'status': metadata.get('status', ''),
                    'posted_date': metadata.get('posted_date', ''),
                    'application_deadline': metadata.get('application_deadline', ''),
                    'total_funding': metadata.get('total_funding', ''),
                    'link': metadata.get('link', ''),
                    'category': metadata.get('category', [])
                })

            formatted_results.append(formatted_result)
        except Exception as e:
            print(f"Error processing match: {e}")
            print(f"Match data: {match}")
            continue

    return jsonify(formatted_results)