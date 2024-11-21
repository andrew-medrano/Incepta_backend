from flask import Blueprint

# Import the individual blueprints
from main.blueprints.home import home_bp
from main.blueprints.search import search_bp
from main.blueprints.about import about_bp

# Optionally, you can define a list of blueprints for easier registration
__all__ = ['home_bp', 'search_bp', 'about_bp']