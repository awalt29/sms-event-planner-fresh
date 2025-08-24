#!/usr/bin/env python3
"""Direct test of validation function with the problematic input from screenshot"""

import os
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging to see validation details
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from app.handlers.guest_availability_handler import GuestAvailabilityHandler

def test_screenshot_case():
    """Test the exact case from the screenshot: 'Saturday 2ydufb'"""
    
    # Create handler with minimal required services
    handler = GuestAvailabilityHandler(None, None, None, None)
    
    print("Testing Screenshot Case: 'Saturday 2ydufb'")
    print("=" * 50)
    
    test_input = "Saturday 2ydufb"
    is_valid = handler._is_valid_availability_input(test_input)
    
    print(f"Input: '{test_input}'")
    print(f"Valid: {is_valid}")
    
    if is_valid:
        print("❌ FAILURE: This should have been rejected!")
        print("❌ The system would accept this gibberish input")
    else:
        print("✅ SUCCESS: Properly rejected gibberish input!")
        print("✅ System will show error message to user")
    
    print("\nComparing with valid input...")
    valid_input = "Saturday afternoon"
    is_valid_good = handler._is_valid_availability_input(valid_input)
    
    print(f"Input: '{valid_input}'")
    print(f"Valid: {is_valid_good}")
    
    if is_valid_good:
        print("✅ SUCCESS: Properly accepted valid input!")
    else:
        print("❌ FAILURE: This should have been accepted!")

if __name__ == "__main__":
    test_screenshot_case()
