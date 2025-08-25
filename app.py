#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""
import os
from app import create_app, db

# Create the Flask application with production config
app = create_app('production')

# Initialize database tables
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")

if __name__ == '__main__':
    # For direct execution (not used with Gunicorn)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
