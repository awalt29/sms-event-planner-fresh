from flask import Flask
from flask_migrate import Migrate
from app.models import db
from app.config import Config


def create_app(config_class=Config):
    """Application factory pattern for creating Flask app instances."""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Create database tables if they don't exist (for production)
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created/verified successfully")
        except Exception as e:
            app.logger.error(f"Error creating database tables: {e}")
    
    # Register blueprints
    from app.routes.sms import sms_bp
    from app.routes.dashboard import dashboard_bp
    
    app.register_blueprint(sms_bp, url_prefix='/sms')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    
    return app
