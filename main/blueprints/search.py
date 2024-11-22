from flask import Blueprint, request, jsonify, current_app
from main.services.search_service import SemanticSearch
from main.constants.agency_codes import get_agency_info
from main.constants.university_codes import get_university_info

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
                'metadata': {}
            }
            
            if index_name == 'tech':
                uni_info = get_university_info(metadata.get('university', ''))
                formatted_result['metadata'].update({
                    'university': uni_info['name'],
                    'university_logo': uni_info['logo'],
                })
            else:
                agency_code = metadata.get('agency_code', '').split('-')[0].strip()  # Get base agency code
                agency_info = get_agency_info(agency_code)
                formatted_result['metadata'].update({
                    'agency_name': agency_info['name'],
                    'agency_logo': agency_info['logo'],
                })

            formatted_results.append(formatted_result)
        except Exception as e:
            print(f"Error processing match: {e}")
            print(f"Match data: {match}")
            continue

    return jsonify(formatted_results)