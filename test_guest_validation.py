#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/aaronwalters/Planner_app_live/Planner_v2')

from app import create_app
from app.handlers.guest_collection_handler import GuestCollectionHandler

def test_guest_validation():
    print("Testing guest parsing validation...")
    print("=" * 50)
    
    # Create a handler instance for testing (just need the parsing methods)
    handler = GuestCollectionHandler.__new__(GuestCollectionHandler)
    
    # Test cases
    test_cases = [
        ("Alex", "Should reject - no phone"),
        ("Sarah and Mike", "Should reject - no phone"),
        ("John Doe, 111-555-1234", "Should accept - has phone"),
        ("Mary 5105935336", "Should accept - has phone"),
        ("Alex Smith", "Should reject - no phone"),
    ]
    
    for test_input, expected in test_cases:
        print(f"\nTesting: '{test_input}' - {expected}")
        
        # Test regex parsing directly
        result = handler._regex_parse_guest(test_input)
        print(f"Regex result: {result}")
        
        # Check validation
        if result.get('success'):
            guests = result.get('guests', [])
            all_have_phone = all(guest.get('phone') for guest in guests)
            print(f"All guests have phone: {all_have_phone}")
            if not all_have_phone:
                print("❌ VALIDATION FAILED - guests without phone numbers allowed")
            else:
                print("✅ VALIDATION PASSED - all guests have phone numbers")
        else:
            print(f"✅ CORRECTLY REJECTED - {result.get('error', 'No error message')}")
        
        print("-" * 30)

if __name__ == "__main__":
    test_guest_validation()
