AGENCY_INFO = {
    'AC': {
        'name': 'AmeriCorps',
        'logo': 'static/grant_agency_logos/AC.png'
    },
    'DHS': {
        'name': 'Department of Homeland Security',
        'logo': 'static/grant_agency_logos/DHS.png'
    },
    'DOC': {
        'name': 'Department of Commerce',
        'logo': 'static/grant_agency_logos/DOC.png'
    },
    'DOD': {
        'name': 'Department of Defense',
        'logo': 'static/grant_agency_logos/DOD.png'
    },
    'DOE': {
        'name': 'Department of Energy',
        'logo': 'static/grant_agency_logos/DOE.png'
    },
    'DOI': {
        'name': 'Department of Interior',
        'logo': 'static/grant_agency_logos/DOI.png'
    },
    'DOL': {
        'name': 'Department of Labor',
        'logo': 'static/grant_agency_logos/DOL.png'
    },
    'DOS': {
        'name': 'Department of State',
        'logo': 'static/grant_agency_logos/DOS.png'
    },
    'DOT': {
        'name': 'Department of Transportation',
        'logo': 'static/grant_agency_logos/DOT.png'
    },
    'ED': {
        'name': 'Department of Education',
        'logo': 'static/grant_agency_logos/ED.png'
    },
    'EPA': {
        'name': 'Environmental Protection Agency',
        'logo': 'static/grant_agency_logos/EPA.png'
    },
    'HHS': {
        'name': 'Department of Health and Human Services',
        'logo': 'static/grant_agency_logos/HHS.png'
    },
    'HUD': {
        'name': 'Department of Housing and Urban Development',
        'logo': 'static/grant_agency_logos/HUD.png'
    },
    'IMLS': {
        'name': 'Institute of Museum and Library Services',
        'logo': 'static/grant_agency_logos/IMLS.png'
    },
    'IVV': {
        'name': 'TEST: NOT A REAL AGENCY',
        'logo': 'static/grant_agency_logos/IVV.png'
    },
    'MCC': {
        'name': 'Millennium Challenge Corporation',
        'logo': 'static/grant_agency_logos/MCC.png'
    },
    'NASA': {
        'name': 'National Aeronautics and Space Administration',
        'logo': 'static/grant_agency_logos/NASA.png'
    },
    'NEA': {
        'name': 'National Endowment for the Arts',
        'logo': 'static/grant_agency_logos/NEA.png'
    },
    'NEH': {
        'name': 'National Endowment for the Humanities',
        'logo': 'static/grant_agency_logos/NEH.png'
    },
    'NSF': {
        'name': 'National Science Foundation',
        'logo': 'static/grant_agency_logos/NSF.png'
    },
    'PAMS': {
        'name': 'DOE Portfolio Analysis and Management System',
        'logo': 'static/grant_agency_logos/PAMS.png'
    },
    'SCRC': {
        'name': 'Southeast Crescent Regional Commission',
        'logo': 'static/grant_agency_logos/SCRC.png'
    },
    'USAID': {
        'name': 'United States Agency for International Development',
        'logo': 'static/grant_agency_logos/USAID.png'
    },
    'USDA': {
        'name': 'United States Department of Agriculture',
        'logo': 'static/grant_agency_logos/USDA.png'
    },
    'USDOJ': {
        'name': 'United States Department of Justice',
        'logo': 'static/grant_agency_logos/USDOJ.png'
    },
    'USDOT': {
        'name': 'United States Department of Transportation',
        'logo': 'static/grant_agency_logos/USDOT.png'
    },
    'VA': {
        'name': 'Department of Veterans Affairs',
        'logo': 'static/grant_agency_logos/VA.png'
    }
}

# Helper function to get agency info with defaults
def get_agency_info(code):
    return AGENCY_INFO.get(code, {
        'name': 'TEST: NOT A REAL AGENCY',
        'logo': 'static/grant_agency_logos/IVV.png'
    })