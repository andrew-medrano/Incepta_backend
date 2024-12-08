UNIVERSITY_INFO = {
    'Stanford University': {
        'name': 'Stanford University',
        'logo': 'static/university_logos/stanford.png',
        'tech_transfer_office': 'Stanford Office of Technology Licensing',
        'website': 'https://techfinder.stanford.edu/'
    },
    'MIT': {
        'name': 'Massachusetts Institute of Technology',
        'logo': 'static/university_logos/mit.png',
        'tech_transfer_office': 'MIT Technology Licensing Office',
        'website': 'https://tlo.mit.edu/'
    },
    'Columbia': {
        'name': 'Columbia University',
        'logo': 'static/university_logos/columbia.png',
        'tech_transfer_office': 'Columbia University Technology Ventures',
        'website': 'https://techventures.columbia.edu/'
    },
    'University of Pennsylvania': {
        'name': 'University of Pennsylvania',
        'logo': 'static/university_logos/upenn.png',
        'tech_transfer_office': 'University of Pennsylvania Technology Transfer Office',
        'website': 'https://upenn.technologypublisher.com/'
    }
}

# Helper function to get university info with defaults
def get_university_info(code):
    return UNIVERSITY_INFO.get(code, {
        'name': 'Unknown University',
        'logo': 'static/university_logos/default.png',
        'tech_transfer_office': 'Technology Transfer Office',
        'website': None
    })
