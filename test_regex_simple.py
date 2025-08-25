#!/usr/bin/env python3
"""Simple regex test for availability parsing"""

import re

def test_validation_patterns():
    """Test if 'Friday 7-11p' matches validation patterns"""
    
    message = "Friday 7-11p"
    message_lower = message.lower().strip()
    print(f"Testing input: '{message}' -> '{message_lower}'")
    
    # Pattern that should match day + time range with AM/PM (UPDATED)
    pattern = r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+\d{1,2}(:\d{2})?\s*(am?|pm?)?\s*(-|to)\s*\d{1,2}(:\d{2})?\s*(am?|pm?)\b'
    
    match = re.search(pattern, message_lower)
    print(f"Current pattern match result: {match}")
    if match:
        print(f"Match groups: {match.groups()}")
    else:
        print("No match found!")
        
    # Test individual components
    print("\nTesting components:")
    day_pattern = r'\b(friday)\b'
    time_pattern = r'\d{1,2}\s*-\s*\d{1,2}'
    ampm_pattern = r'(am|pm)'
    single_ampm_pattern = r'[ap]'
    
    print(f"Day pattern: {re.search(day_pattern, message_lower)}")
    print(f"Time range pattern: {re.search(time_pattern, message_lower)}")
    print(f"AM/PM pattern: {re.search(ampm_pattern, message_lower)}")
    print(f"Single letter am/pm: {re.search(single_ampm_pattern, message_lower)}")
    
    # Test a modified pattern that accepts single letter am/pm
    better_pattern = r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+\d{1,2}(:\d{2})?\s*(am?|pm?)?\s*(-|to)\s*\d{1,2}(:\d{2})?\s*(am?|pm?)\b'
    better_match = re.search(better_pattern, message_lower)
    print(f"Better pattern match: {better_match}")
    
    # Even more flexible pattern
    flexible_pattern = r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+\d{1,2}\s*-\s*\d{1,2}[ap]m?\b'
    flexible_match = re.search(flexible_pattern, message_lower)
    print(f"Flexible pattern match: {flexible_match}")
    
    if flexible_match:
        print(f"Flexible match groups: {flexible_match.groups()}")

def test_shorthand_time_parsing():
    """Test shorthand time parsing logic"""
    spec = "7-11p"
    
    # Mimic the _parse_shorthand_time method logic
    range_pattern = r'(\d{1,2})\s*-\s*(\d{1,2})\s*([ap]m?)?'
    range_match = re.search(range_pattern, spec)
    
    print(f"\nTesting shorthand parsing on '{spec}':")
    print(f"Range pattern match: {range_match}")
    
    if range_match:
        start_num = int(range_match.group(1))
        end_num = int(range_match.group(2))
        suffix = range_match.group(3)
        
        print(f"Start: {start_num}, End: {end_num}, Suffix: '{suffix}'")
        
        if suffix and 'p' in suffix:
            # Both times are PM
            start_hour = 12 if start_num == 12 else start_num + 12
            end_hour = 12 if end_num == 12 else end_num + 12
            print(f"PM interpretation: {start_hour}:00 - {end_hour}:00")

if __name__ == "__main__":
    print("=== Testing Availability Parsing for 'Friday 7-11p' ===")
    test_validation_patterns()
    test_shorthand_time_parsing()
