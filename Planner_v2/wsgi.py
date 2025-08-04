#!/usr/bin/env python3
"""
WSGI entry point for production deployment
"""
import os
import sys

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

print(f"WSGI starting from directory: {current_dir}")
print(f"Python path: {sys.path}")

from app import create_app, db

# Create the Flask application with production config
app = create_app('production')
print("Flask app created successfully")

# Initialize database tables
with app.app_context():
    try:
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")

if __name__ == '__main__':
    # For direct execution (not used with Gunicorn)
    app.run(host='0.0.0.0', port=8080)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
