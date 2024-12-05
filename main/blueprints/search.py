from flask import Blueprint, request, jsonify, current_app, render_template
from main.services.search_service import SemanticSearch
from main.constants.agency_codes import get_agency_info
from main.constants.university_codes import get_university_info
from main.constants.metadata_fields import (
    TECH_METADATA_FIELDS,
    GRANTS_METADATA_FIELDS,
    COMMON_METADATA_FIELDS
)
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import requests
import logging
import re

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
                'metadata': {
                    'llm_teaser': metadata.get('llm_teaser', '')
                }
            }
            
            if index_name == 'tech':
                uni_info = get_university_info(metadata.get('university', ''))
                formatted_result['metadata'].update({
                    'university': uni_info['name'] if uni_info else 'Unknown University',
                    'university_logo': uni_info['logo'] if uni_info else '/static/images/default_university.png',
                })
            else:
                agency_code = metadata.get('agency_code', '').split('-')[0].strip()
                agency_info = get_agency_info(agency_code)
                formatted_result['metadata'].update({
                    'agency_name': agency_info['name'] if agency_info else 'Unknown Agency',
                    'agency_logo': agency_info['logo'] if agency_info else '/static/images/default_agency.png',
                })

            formatted_results.append(formatted_result)
        except Exception as e:
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
    result['metadata']['llm_summary'] = result['metadata']['llm_summary'].replace('\\n', '\n')
    
    # change words in **bold** to <b>bold</b>
    result['metadata']['llm_summary'] = re.sub(r'\*\*([^\*]+)\*\*', r'<b>\1</b>', result['metadata']['llm_summary'])

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
        # check if award_ceiling or award_floor actually contain numeric characters
        if not result['metadata']['award_ceiling'].isdigit():
            result['metadata']['award_ceiling'] = ''
        if not result['metadata']['award_floor'].isdigit():
            result['metadata']['award_floor'] = ''

        agency_code = result['metadata'].get('agency_code', '').split('-')[0].strip()
        agency_info = get_agency_info(agency_code)
        result['metadata'].update({
            'agency_name': agency_info['name'],
            'agency_logo': agency_info['logo']
        })
        
    return render_template(
        'result_detail.html',
        result=result,
        index=index,
        metadata_fields=TECH_METADATA_FIELDS if index == 'tech' else GRANTS_METADATA_FIELDS,
        common_fields=COMMON_METADATA_FIELDS
    )

@search_bp.route('/submit-contact', methods=['POST'])
def submit_contact():
    data = request.json
    
    # Format the message for Slack using the simpler text-based format
    slack_message = {
        "text": (
            f"New {data['itemType']} Inquiry\n\n"
            f"From: {data['name']}\n"
            f"Email: {data['email']}\n"
            f"Company: {data['company']}\n"
            f"Phone: {data['phone']}\n\n"
            f"Item Title: {data['itemTitle']}\n"
            f"Message: {data['message']}"
        )
    }

    try:
        logging.info(f"Sending Slack notification for inquiry from {data['email']}")
        response = requests.post(
            os.getenv('SLACK_WEBHOOK_URL'),
            json=slack_message
        )
        
        if response.status_code == 200:
            logging.info("Slack notification sent successfully")
            return jsonify({"success": True})
        else:
            logging.error(f"Slack API error: {response.status_code} - {response.text}")
            return jsonify({"success": False}), 500
            
    except Exception as e:
        logging.error(f"Error sending Slack notification: {str(e)}")
        return jsonify({"success": False}), 500