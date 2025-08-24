#!/usr/bin/env python3
"""Test the validation function directly"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_validation_only():
    """Test just the validation logic"""
    
    # Test the validation patterns directly
    import re
    
    message = "friday 7-11p"
    
    # The exact patterns from the updated code
    valid_patterns = [
        # Day + time period: "monday morning", "saturday afternoon"
        r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(morning|afternoon|evening|night)\b',
        
        # Day + "all day": "saturday all day", "monday allday"
        r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(all\s*day)\b',
        
        # Day + specific time: "monday 2pm", "saturday 6am", "friday 10:30am", "friday 7p"
        r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+\d{1,2}(:\d{2})?\s*(am?|pm?)\b',
        
        # Day + time range with AM/PM: "monday 2-6pm", "saturday 9am-5pm", "friday 2pm to 8pm", "friday 7-11p"
        r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+\d{1,2}(:\d{2})?\s*(am?|pm?)?\s*(-|to)\s*\d{1,2}(:\d{2})?\s*(am?|pm?)\b',
        
        # Day + time range without AM/PM: "friday 2-4", "monday 9-5"
        r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+\d{1,2}\s*-\s*\d{1,2}\b',
        
        # Day + "from" + time range: "friday from 2-4", "monday from 9am-5pm"
        r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+from\s+\d{1,2}(:\d{2})?\s*(am?|pm?)?\s*(-|to)\s*\d{1,2}(:\d{2})?\s*(am?|pm?)?\b',
        
        # Day + "after/before time": "monday after 2pm", "saturday before 6pm", "friday after 7p"
        r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(after|before)\s+\d{1,2}(:\d{2})?\s*(am?|pm?)\b',
        
        # Just time periods: "morning", "afternoon", "evening", "all day" (always allowed)
        r'^\s*(morning|afternoon|evening|night|all\s*day)\s*$'
    ]
    
    print(f"Testing validation for: '{message}'")
    
    for i, pattern in enumerate(valid_patterns):
        match = re.search(pattern, message)
        print(f"Pattern {i+1}: {'✅ MATCH' if match else '❌ NO MATCH'}")
        if match:
            print(f"   Groups: {match.groups()}")
            print(f"   Pattern: {pattern}")
            break
    
    # Overall validation result
    any_match = any(re.search(pattern, message) for pattern in valid_patterns)
    print(f"\n🎯 Overall validation: {'✅ PASS' if any_match else '❌ FAIL'}")

if __name__ == "__main__":
    test_validation_only()
