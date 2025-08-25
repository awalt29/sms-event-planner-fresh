#!/usr/bin/env python3
"""
Database initialization script for production deployment
"""

import os
from app import create_app, db

def init_db():
    """Initialize database tables"""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Test database connection
        from app.models.planner import Planner
        test_planner = Planner.query.first()
        print("✅ Database connection tested successfully!")

if __name__ == "__main__":
    init_db()
