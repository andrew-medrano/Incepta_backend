from flask import Blueprint, request, jsonify, current_app, render_template
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
                'id': match['id'],
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
                agency_code = metadata.get('agency_code', '').split('-')[0].strip()
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

@search_bp.route('/result/<index>/<id>')
def result_detail(index, id):
    ss = current_app.config['SEMANTIC_SEARCH']
    if index != ss.index_name:
        ss.set_index(index)
    
    # Fetch the specific result from Pinecone
    result = ss.get_by_id(id)

    # change newlines in description metadata to <br>
    result['metadata']['description'] = result['metadata']['description'].replace('\\n', '\n')
    
    if not result:
        return "Result not found", 404
    
    # Add the logo and name information to the metadata
    if index == 'tech':
        uni_info = get_university_info(result['metadata'].get('university', ''))
        result['metadata'].update({
            'university': uni_info['name'],
            'university_logo': uni_info['logo']
        })
    else:
        agency_code = result['metadata'].get('agency_code', '').split('-')[0].strip()
        agency_info = get_agency_info(agency_code)
        result['metadata'].update({
            'agency_name': agency_info['name'],
            'agency_logo': agency_info['logo']
        })
        
    return render_template('result_detail.html', result=result, index=index)