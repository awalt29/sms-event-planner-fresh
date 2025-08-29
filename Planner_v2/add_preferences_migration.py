#!/usr/bin/env python3
"""
Add preferences fields to Guest model
"""
import sqlite3
import os

def add_preferences_columns():
    """Add preferences columns to guests table"""
    
    # Check if we're using SQLite or PostgreSQL
    if os.path.exists('planner.db'):
        # SQLite (development)
        conn = sqlite3.connect('planner.db')
        cursor = conn.cursor()
        
        try:
            # Add preferences_provided column
            cursor.execute("ALTER TABLE guests ADD COLUMN preferences_provided BOOLEAN DEFAULT FALSE")
            print("✅ Added preferences_provided column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("⚠️  preferences_provided column already exists")
            else:
                raise
        
        try:
            # Add preferences column  
            cursor.execute("ALTER TABLE guests ADD COLUMN preferences TEXT")
            print("✅ Added preferences column")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print("⚠️  preferences column already exists")
            else:
                raise
        
        conn.commit()
        conn.close()
        print("✅ SQLite database updated successfully!")
        
    else:
        print("⚠️  No SQLite database found. For PostgreSQL (production), run this manually:")
        print("ALTER TABLE guests ADD COLUMN preferences_provided BOOLEAN DEFAULT FALSE;")
        print("ALTER TABLE guests ADD COLUMN preferences TEXT;")

if __name__ == "__main__":
    add_preferences_columns()
