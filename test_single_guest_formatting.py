#!/usr/bin/env python3
"""Test time formatting in single guest overlap view"""

from app import create_app
from app.services.message_formatting_service import MessageFormattingService
from datetime import date

app = create_app()

def test_single_guest_formatting():
    """Test that single guest times are formatted correctly"""
    with app.app_context():
        print("🧪 Testing Single Guest Time Formatting")
        print("=" * 42)
        
        # Simulate the overlap data that would be returned
        single_guest_overlap = [{
            'date': date(2025, 8, 30),
            'start_time': '14:00',  # Military time from service
            'end_time': '18:00',
            'available_guests': ['Aaron'],
            'guest_count': 1
        }]
        
        # Test formatting 
        formatter = MessageFormattingService()
        formatted_message = formatter.format_time_selection_options(single_guest_overlap)
        
        print("📱 Formatted SMS Message:")
        print("=" * 30)
        print(formatted_message)
        print("=" * 30)
        
        # Check for 12-hour format
        if "2pm" in formatted_message or "14:00" in formatted_message:
            if "2pm" in formatted_message:
                print("✅ Time is correctly formatted in 12-hour format (2pm)")
            else:
                print("❌ Time is still in military format (14:00)")
        else:
            print("❓ Time format unclear - check message above")
        
        print("✅ Test complete!")

if __name__ == "__main__":
    test_single_guest_formatting()
