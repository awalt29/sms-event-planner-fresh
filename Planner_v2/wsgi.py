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
                print(f"🔍 DATABASE DEBUG INFO:")
                print(f"   INITIALIZE_DB environment variable: {os.getenv('INITIALIZE_DB', 'not set')}")
                print(f"   INITIALIZE_DB parsed value: {INITIALIZE_DB}")
                print(f"   DATABASE_URL: {os.getenv('DATABASE_URL', 'not set')}")
                print("🛡️  INITIALIZE_DB=false - Attempting to preserve existing data...")
                
                # Check if tables actually exist (not just database connection)
                try:
                    # Try to query a table that should exist if database is initialized
                    with db.engine.connect() as conn:
                        result = conn.execute(db.text('SELECT COUNT(*) FROM planners'))
                        count = result.scalar()
                        print(f"✅ Database tables exist - existing data preserved")
                except Exception as table_error:
                    # Tables don't exist - this is a new deployment, create them
                    error_msg = str(table_error).lower()
                    if any(phrase in error_msg for phrase in ["does not exist", "no such table", "relation does not exist"]):
                        print("🆕 Tables don't exist - creating database schema for new deployment...")
                        db.create_all()
                        print("✅ Database tables created for new deployment")
                    else:
                        print(f"❌ Unexpected database error: {table_error}")
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
