from flask import Flask

def create_app(ss):
    app = Flask(__name__)

    # Delayed import of blueprints
    from main.blueprints.home import home_bp
    from main.blueprints.search import search_bp
    from main.blueprints.about import about_bp

    # Register blueprints
    app.register_blueprint(home_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(about_bp)

    # Add SemanticSearch instance to app configuration
    app.config['SEMANTIC_SEARCH'] = ss

    return app