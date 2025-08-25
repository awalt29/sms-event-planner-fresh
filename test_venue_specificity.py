#!/usr/bin/env python3
"""
Test venue suggestion specificity improvements
Testing if venues returned are actually known for the requested activity
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.venue_service import VenueService
import json

def test_darts_specificity():
    """Test that darts venues are actually known for darts"""
    print("\n🎯 Testing darts venue specificity in Tribeca...")
    
    venue_service = VenueService()
    result = venue_service.get_venue_suggestions("darts", "tribeca")
    
    print(f"Result: {json.dumps(result, indent=2)}")
    
    if result.get('success') and result.get('venues'):
        venues = result['venues']
        print(f"\nFound {len(venues)} venue suggestions:")
        
        for i, venue in enumerate(venues, 1):
            name = venue.get('name', 'Unknown')
            description = venue.get('description', 'No description')
            link = venue.get('link', 'No link')
            
            print(f"\n{i}. {name}")
            print(f"   Description: {description}")
            print(f"   Link: {link}")
            
            # Check if description suggests darts specialization
            darts_keywords = ['dart', 'bulls', 'throw', 'board', 'pub']
            desc_lower = description.lower()
            has_darts_context = any(keyword in desc_lower for keyword in darts_keywords)
            
            if has_darts_context:
                print(f"   ✅ Description suggests darts specialization")
            else:
                print(f"   ⚠️  Description doesn't clearly indicate darts specialization")
    else:
        print(f"❌ Failed to get venues: {result}")

def test_bowling_specificity():
    """Test bowling venue specificity"""
    print("\n🎳 Testing bowling venue specificity in Manhattan...")
    
    venue_service = VenueService()
    result = venue_service.get_venue_suggestions("bowling", "manhattan")
    
    if result.get('success') and result.get('venues'):
        venues = result['venues']
        print(f"Found {len(venues)} bowling venue suggestions:")
        
        for i, venue in enumerate(venues, 1):
            name = venue.get('name', 'Unknown')
            description = venue.get('description', 'No description')
            
            print(f"{i}. {name}: {description}")
            
            # Check if it's actually a bowling alley
            bowling_keywords = ['bowl', 'alley', 'lane', 'strike', 'pin']
            desc_lower = description.lower()
            has_bowling_context = any(keyword in desc_lower for keyword in bowling_keywords)
            
            if has_bowling_context:
                print(f"   ✅ Appears to be an actual bowling venue")
            else:
                print(f"   ⚠️  May not be a dedicated bowling venue")
    else:
        print(f"❌ Failed to get bowling venues: {result}")

def test_karaoke_specificity():
    """Test karaoke venue specificity"""
    print("\n🎤 Testing karaoke venue specificity in East Village...")
    
    venue_service = VenueService()
    result = venue_service.get_venue_suggestions("karaoke", "east village")
    
    if result.get('success') and result.get('venues'):
        venues = result['venues']
        print(f"Found {len(venues)} karaoke venue suggestions:")
        
        for i, venue in enumerate(venues, 1):
            name = venue.get('name', 'Unknown')
            description = venue.get('description', 'No description')
            
            print(f"{i}. {name}: {description}")
            
            # Check if it's actually known for karaoke
            karaoke_keywords = ['karaoke', 'sing', 'private room', 'booth', 'mic']
            desc_lower = description.lower()
            has_karaoke_context = any(keyword in desc_lower for keyword in karaoke_keywords)
            
            if has_karaoke_context:
                print(f"   ✅ Appears to be a karaoke-focused venue")
            else:
                print(f"   ⚠️  May not be a dedicated karaoke venue")
    else:
        print(f"❌ Failed to get karaoke venues: {result}")

if __name__ == "__main__":
    print("🧪 Testing Venue Suggestion Specificity")
    print("=" * 50)
    
    try:
        test_darts_specificity()
        test_bowling_specificity() 
        test_karaoke_specificity()
        
        print("\n" + "=" * 50)
        print("✅ Venue specificity testing complete!")
        print("\nThis test checks if venue suggestions are actually known for the requested activity")
        print("rather than just generic establishments that might have the activity available.")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
