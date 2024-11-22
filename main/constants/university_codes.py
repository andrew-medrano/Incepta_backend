UNIVERSITY_INFO = {
    'Stanford University': {
        'name': 'Stanford University',
        'logo': 'static/university_logos/stanford.png',
        'tech_transfer_office': 'Stanford Office of Technology Licensing',
        'website': 'https://techfinder.stanford.edu/'
    }
}

# Helper function to get university info with defaults
def get_university_info(code):
    return UNIVERSITY_INFO.get(code.upper(), {
        'name': 'Unknown University',
        'logo': 'static/university_logos/default.png',
        'tech_transfer_office': 'Technology Transfer Office',
        'website': None
    })
