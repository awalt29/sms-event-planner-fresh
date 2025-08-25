#!/usr/bin/env python3
"""Test the SMS message formatting for overlap display"""

from app import create_app
from app.services.message_formatting_service import MessageFormattingService
from datetime import date

app = create_app()

def test_message_formatting():
    """Test how overlap times appear in actual SMS messages"""
    with app.app_context():
        print("🧪 Testing SMS Message Formatting")
        print("=" * 40)
        
        # Create sample overlaps like our debug scenario
        overlaps = [
            {
                'date': date(2025, 8, 30),  # Saturday
                'start_time': '16:00',      # Military time from availability_service
                'end_time': '23:59',
                'available_guests': ['A A Ron', 'Aaron'],
                'guest_count': 2
            },
            {
                'date': date(2025, 8, 31),  # Sunday
                'start_time': '08:00',      # All-day overlap
                'end_time': '23:59',
                'available_guests': ['A A Ron', 'Aaron'], 
                'guest_count': 2
            }
        ]
        
        # Test message formatting service
        formatter = MessageFormattingService()
        message = formatter.format_time_selection_options(overlaps)
        
        print("📱 SMS Message Preview:")
        print("-" * 30)
        print(message)
        print("-" * 30)
        
        print("✅ Test complete!")

if __name__ == "__main__":
    test_message_formatting()
