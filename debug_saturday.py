#!/usr/bin/env python3
"""Test Saturday date calculation"""

from datetime import datetime, timedelta

def test_saturday_calculation():
    # Today is Sunday, August 10, 2025 (weekday 6)
    today = datetime(2025, 8, 10)  # Sunday
    print(f"Today: {today.strftime('%A, %B %d, %Y')} (weekday {today.weekday()})")
    
    text_lower = "saturday"
    
    # Current logic
    days_until_saturday = (5 - today.weekday()) % 7
    print(f"Days until Saturday calculation: (5 - {today.weekday()}) % 7 = {days_until_saturday}")
    
    if days_until_saturday == 0 and today.hour > 12:
        days_until_saturday = 7
        print(f"Adjusted to next Saturday: {days_until_saturday}")
    
    saturday = today + timedelta(days=days_until_saturday)
    print(f"Result Saturday: {saturday.strftime('%A, %B %d, %Y')}")
    
    # The issue: when today is Sunday (weekday 6), 
    # (5 - 6) % 7 = (-1) % 7 = 6
    # So it's going 6 days forward from Sunday = Saturday
    # But that's NEXT Saturday, not the previous one
    
    print("\n--- Expected vs Actual ---")
    print(f"Expected: Saturday, August 16, 2025 (next Saturday)")
    print(f"Actual: {saturday.strftime('%A, %B %d, %Y')}")
    
    # Let me check what the correct calculation should be
    # For next Saturday from Sunday: should be 6 days ahead
    # Saturday is weekday 5, Sunday is weekday 6
    # So next Saturday is (5 - 6 + 7) % 7 = 6 days ahead ✓
    
    print(f"\nThe calculation is actually correct!")
    print(f"Next Saturday from Sunday August 10 should be August 16")
    print(f"6 days from August 10 = August 16 ✓")

if __name__ == "__main__":
    test_saturday_calculation()
