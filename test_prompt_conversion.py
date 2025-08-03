#!/usr/bin/env python3

import os
import sys
sys.path.insert(0, '/Users/aaronwalters/Planner_app_live')

# Test the prompt conversion logic
def test_prompt_conversion():
    """Test the food -> restaurant conversion in the prompt"""
    
    print("🔍 Testing prompt conversion logic...")
    print("=" * 50)
    
    test_cases = [
        "chinese food",
        "chinese", 
        "italian food",
        "thai food",
        "bar",
        "coffee shop"
    ]
    
    for activity in test_cases:
        print(f"\nInput: '{activity}'")
        
        # Apply the same logic as in the AI service
        if 'food' in activity.lower():
            cuisine = activity.lower().replace(' food', '').strip()
            prompt_activity = f"{cuisine.title()} restaurants"
        else:
            prompt_activity = activity
            
        print(f"Prompt will ask for: '{prompt_activity}'")
        print(f"Expected: {'✅ Good' if 'restaurants' in prompt_activity or 'food' not in activity else '❌ Still has food'}")

if __name__ == "__main__":
    test_prompt_conversion()
