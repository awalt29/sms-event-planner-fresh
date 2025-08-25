#!/usr/bin/env python3
"""Test script to debug availability parsing for 'Friday 7-11p'"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.handlers.guest_availability_handler import GuestAvailabilityHandler
from app.models.guest_state import GuestState
from app.models.event import Event
from app.models.planner import Planner
from datetime import datetime, timedelta
import re

def test_validation_patterns():
    """Test if 'Friday 7-11p' matches validation patterns"""
    
    message = "Friday 7-11p"
    message_lower = message.lower().strip()
    print(f"Testing input: '{message}' -> '{message_lower}'")
    
    # Pattern that should match day + time range with AM/PM
    pattern = r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+\d{1,2}(:\d{2})?\s*(am|pm)?\s*(-|to)\s*\d{1,2}(:\d{2})?\s*(am|pm)\b'
    
    match = re.search(pattern, message_lower)
    print(f"Pattern match result: {match}")
    if match:
        print(f"Match groups: {match.groups()}")
    else:
        print("No match found!")
        
    # Test individual components
    print("\nTesting components:")
    print(f"Day pattern: {re.search(r'\b(friday)\b', message_lower)}")
    print(f"Time range pattern: {re.search(r'\d{1,2}\s*-\s*\d{1,2}', message_lower)}")
    print(f"AM/PM pattern: {re.search(r'(am|pm)', message_lower)}")
    
    # Test the specific shorthand format
    shorthand_pattern = r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+\d{1,2}\s*-\s*\d{1,2}\s*[ap]\b'
    shorthand_match = re.search(shorthand_pattern, message_lower)
    print(f"Shorthand pattern match: {shorthand_match}")

def test_shorthand_time_parsing():
    """Test the _parse_shorthand_time method directly"""
    from app.handlers.guest_availability_handler import GuestAvailabilityHandler
    from app.services.event_workflow_service import EventWorkflowService
    from app.services.guest_management_service import GuestManagementService
    from app.services.message_formatting_service import MessageFormattingService
    from app.services.ai_processing_service import AIProcessingService
    
    # Initialize handler
    handler = GuestAvailabilityHandler(
        EventWorkflowService(),
        GuestManagementService(),
        MessageFormattingService(),
        AIProcessingService()
    )
    
    # Test the shorthand parsing
    spec = "7-11p"
    result = handler._parse_shorthand_time(spec)
    print(f"\nTesting _parse_shorthand_time('{spec}'): {result}")
    
    # Test full spec parsing
    spec_full = "friday 7-11p"
    result_full = handler._parse_single_availability_spec(spec_full)
    print(f"Testing _parse_single_availability_spec('{spec_full}'): {result_full}")

if __name__ == "__main__":
    print("=== Testing Availability Parsing for 'Friday 7-11p' ===")
    test_validation_patterns()
    test_shorthand_time_parsing()
