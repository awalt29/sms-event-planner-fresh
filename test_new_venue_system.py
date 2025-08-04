#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.utils.venue_suggestions import suggest_venues

def test_new_venue_system():
    """Test the new venue suggestion system."""
    
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing New Venue Suggestion System")
        print("=" * 50)
        
        test_cases = [
            ("chinese food", "Brooklyn"),
            ("italian restaurant", "Manhattan"), 
            ("coffee", "Queens"),
            ("bar", "Williamsburg"),
            ("brunch", "NYC"),
            ("unknown activity", "random location")
        ]
        
        for activity, location in test_cases:
            print(f"\n🎯 Testing: '{activity}' in '{location}'")
            print("-" * 30)
            
            result = suggest_venues(activity, location)
            print(f"Success: {result.get('success')}")
            print(f"Method: {result.get('method', 'unknown')}")
            
            if result.get('success'):
                venues = result.get('venues', [])
                print(f"Found {len(venues)} venues:")
                for i, venue in enumerate(venues, 1):
                    print(f"  {i}. {venue.get('name', 'Unknown')}")
                    print(f"     {venue.get('description', 'No description')}")
                    print(f"     {venue.get('link', 'No link')}")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
        
        print("\n✅ All tests completed!")

if __name__ == "__main__":
    test_new_venue_system()
