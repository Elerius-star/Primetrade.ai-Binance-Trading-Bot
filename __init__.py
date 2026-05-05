"""
Web Interface Package for Trading Bot
Handles Flask routes and frontend serving
"""

from flask import Flask
from flask_cors import CORS
import os

def create_app(config=None):
    """Application factory for Flask app"""
    app = Flask(__name__, 
                template_folder='.',
                static_folder='.')
    
    # Configure CORS
    CORS(app)
    
    # Load configuration
    if config:
        app.config.update(config)
    
    # Set default settings
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['JSON_SORT_KEYS'] = False
    
    return app

__all__ = ['create_app']