#!/usr/bin/env python3
"""Test the new positive pattern matching approach for availability validation"""

import os
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging to see validation details
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from app.handlers.guest_availability_handler import GuestAvailabilityHandler

def test_pattern_validation():
    """Test the positive pattern matching validation"""
    # Create a mock handler just for testing the validation method
    from app.handlers.guest_availability_handler import GuestAvailabilityHandler
    
    # Create handler with minimal required services
    handler = GuestAvailabilityHandler(None, None, None, None)
    
    print("Testing Positive Pattern Matching")
    print("=" * 50)
    
    # Test cases that SHOULD be accepted
    valid_inputs = [
        "Monday morning",
        "Saturday afternoon", 
        "Friday evening",
        "Sunday all day",
        "Monday 2pm",
        "Saturday 6am",
        "Friday 10:30am",
        "Monday 2-6pm",
        "Saturday 9am-5pm", 
        "Friday 2pm to 8pm",
        "Monday after 2pm",
        "Saturday before 6pm",
        "morning",
        "afternoon", 
        "all day",
        "2-6pm",
        "9am-5pm",
        "after 2pm"
    ]
    
    # Test cases that SHOULD be rejected
    invalid_inputs = [
        "Saturday 2ydufb",  # The problematic case from screenshot
        "Monday afuiDbdDbeb",
        "Tuesday xyzabc",
        "asdfghjkl",
        "hello world",
        "random text",
        "123",
        "Saturday garbage",
        "Monday nonsense123",
        "Friday random words here"
    ]
    
    print("VALID INPUTS (should be accepted):")
    print("-" * 30)
    for input_text in valid_inputs:
        is_valid = handler._is_valid_availability_input(input_text)
        status = "✅ PASS" if is_valid else "❌ FAIL"
        print(f"{status}: '{input_text}' -> {is_valid}")
    
    print("\nINVALID INPUTS (should be rejected):")
    print("-" * 30) 
    for input_text in invalid_inputs:
        is_valid = handler._is_valid_availability_input(input_text)
        status = "✅ PASS" if not is_valid else "❌ FAIL"
        print(f"{status}: '{input_text}' -> {is_valid}")

if __name__ == "__main__":
    test_pattern_validation()
