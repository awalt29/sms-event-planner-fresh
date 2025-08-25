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

# Create the Flask application - it will auto-detect environment
try:
    app = create_app()  # Will use 'production' if FLASK_ENV is set, otherwise 'default'
    print("Flask app created successfully")
    
    # DATABASE PERSISTENCE: Only create tables if explicitly requested or on first deploy
    # This prevents accidental data loss during redeployments
    INITIALIZE_DB = os.getenv('INITIALIZE_DB', 'false').lower() == 'true'
    
    with app.app_context():
        try:
            if INITIALIZE_DB:
                print("INITIALIZE_DB=true - Creating database tables...")
                db.create_all()
                print("Database tables created successfully")
            else:
                print("INITIALIZE_DB=false - Preserving existing data, checking database connection...")
                # Verify database connection without destroying data
                try:
                    # Use SQLAlchemy 2.0+ syntax for database connection test
                    with db.engine.connect() as conn:
                        conn.execute(db.text('SELECT 1'))
                    print("Database connection verified - existing data preserved")
                except Exception as connection_error:
                    # Only create tables if database appears completely empty/new
                    if any(phrase in str(connection_error).lower() for phrase in 
                          ["does not exist", "no such table", "relation does not exist"]):
                        print("Database appears new, creating tables...")
                        db.create_all()
                        print("Database tables created for new deployment")
                    else:
                        print(f"Database connection error: {connection_error}")
                        raise
                        
        except Exception as e:
            print(f"Database initialization error: {e}")
            raise
            
except Exception as e:
    print(f"Error creating Flask app: {e}")
    raise  # Re-raise the exception so Railway sees the error

if __name__ == '__main__':
    # For direct execution (not used with Gunicorn)
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
