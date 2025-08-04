from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config
import logging
import os

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV') or 'default'
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Configure logging
    if not app.debug and not app.testing:
        logging.basicConfig(level=logging.INFO)
    
    # Register blueprints
    from app.routes.sms import sms_bp
    app.register_blueprint(sms_bp, url_prefix='/sms')
    
    # Add health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'SMS Event Planner is running'}, 200
    
    @app.route('/')
    def index():
        return {'message': 'SMS Event Planner API', 'version': '2.0', 'status': 'active'}, 200
    
    # Import models to ensure they're registered with SQLAlchemy
    with app.app_context():
        from app.models import planner, event, guest, guest_state, contact, availability
    
    return app
