#!/usr/bin/env python3
"""Test venue suggestion service directly"""

import os
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from app.services.venue_service import VenueService
from app.services.ai_processing_service import AIProcessingService

def test_venue_service():
    """Test venue service functionality"""
    
    print("Testing Venue Service")
    print("=" * 50)
    
    # Test AI service first
    ai_service = AIProcessingService()
    print(f"AI Service API Key Available: {ai_service.api_key is not None}")
    
    if ai_service.api_key:
        print("Testing AI service with simple prompt...")
        test_response = ai_service.make_completion("Say hello", max_tokens=50)
        print(f"AI Response: {test_response}")
    else:
        print("❌ No OpenAI API key - AI features disabled")
    
    print("\n" + "-" * 30)
    
    # Test venue service
    venue_service = VenueService()
    
    # Test cases
    test_cases = [
        ("Darts", "tribeca"),
        ("Coffee", "Manhattan"),
        ("Sushi", "Brooklyn"),
    ]
    
    for activity, location in test_cases:
        print(f"\nTesting: {activity} in {location}")
        print("-" * 20)
        
        try:
            venues = venue_service.get_venue_suggestions(activity, location)
            print(f"Success: Found {len(venues)} venues")
            
            for i, venue in enumerate(venues, 1):
                print(f"{i}. {venue.get('name', 'Unknown')} - {venue.get('description', 'No description')}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_venue_service()
