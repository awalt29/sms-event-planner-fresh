#!/usr/bin/env python3
"""
Database initialization script for production deployment.
This ensures all database tables are created when the app starts.
"""

from app import create_app
from app.models import db
import os

def init_database():
    """Initialize the database with all required tables."""
    app = create_app()
    
    with app.app_context():
        try:
            # Create all database tables
            db.create_all()
            print("✅ Database tables created successfully")
            return True
        except Exception as e:
            print(f"❌ Error creating database tables: {e}")
            return False

if __name__ == "__main__":
    init_database()
