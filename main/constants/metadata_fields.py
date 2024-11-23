TECH_METADATA_FIELDS = {
    'number': {
        'display_name': '',  # Empty means use the value directly
        'type': 'text'
    },
    'patent': {
        'display_name': 'Patents',
        'type': 'text'
    },
    'link': {
        'display_name': 'Original Source',
        'type': 'link'
    }
}

GRANTS_METADATA_FIELDS = {
    'opportunity_number': {
        'display_name': 'Opportunity Number',
        'type': 'text'
    },
    'status': {
        'display_name': 'Status',
        'type': 'text'
    },
    'posted_date': {
        'display_name': 'Posted Date',
        'type': 'date'
    },
    'last_updated_date': {
        'display_name': 'Last Updated',
        'type': 'date'
    },
    'close_date': {
        'display_name': 'Close Date',
        'type': 'date'
    },
    'application_deadline': {
        'display_name': 'Application Deadline',
        'type': 'date'
    },
    'total_funding': {
        'display_name': 'Total Funding',
        'type': 'currency'
    },
    'award_ceiling': {
        'display_name': 'Award Ceiling',
        'type': 'currency'
    },
    'award_floor': {
        'display_name': 'Award Floor',
        'type': 'currency'
    },
    'link': {
        'display_name': 'View original source',
        'type': 'link'
    }
}

# Common fields that appear in both types
COMMON_METADATA_FIELDS = {
    'category': {
        'display_name': 'Categories',
        'type': 'list'
    }
}