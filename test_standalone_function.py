#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.ai import suggest_venues

def test_standalone_suggest_venues():
    """Test the standalone suggest_venues function that SMS routes actually use."""
    
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing standalone suggest_venues function...")
        
        # Test the food conversion in the standalone function
        print("\n1. Testing 'chinese food' conversion:")
        result = suggest_venues("chinese food", "Brooklyn")
        print(f"Result: {result}")
        
        print("\n2. Testing 'italian food' conversion:")
        result = suggest_venues("italian food", "Manhattan") 
        print(f"Result: {result}")
        
        print("\n3. Testing 'chinese' (no food):")
        result = suggest_venues("chinese", "Brooklyn")
        print(f"Result: {result}")
        
        print("\n✅ Standalone function tests complete!")

if __name__ == "__main__":
    test_standalone_suggest_venues()
