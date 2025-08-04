#!/usr/bin/env python3
"""
Production entry point for the SMS Event Planner application.
Used by Railway and other deployment platforms.
"""
import os
from app import create_app, db

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    # For Railway deployment, use PORT environment variable
    port = int(os.environ.get('PORT', 5000))
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    # Run the application
    app.run(host='0.0.0.0', port=port, debug=False)
