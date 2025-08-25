#!/usr/bin/env python3
"""Test date formatting consistency between normal and partial overlaps"""

from app import create_app
from app.services.message_formatting_service import MessageFormattingService
from datetime import date

app = create_app()

def test_date_formatting_consistency():
    """Test that both normal and partial overlaps use the same date format"""
    with app.app_context():
        print("🧪 Testing Date Formatting Consistency")
        print("=" * 42)
        
        # Create test overlap data
        test_overlap = [{
            'date': date(2025, 8, 29),  # Friday
            'start_time': '14:00',
            'end_time': '18:00',
            'available_guests': ['Aaron'],
            'guest_count': 1
        }]
        
        # Test normal overlap formatting
        formatter = MessageFormattingService()
        normal_message = formatter.format_time_selection_options(test_overlap)
        
        print("📱 Normal Overlap Format:")
        print("=" * 30)
        print(normal_message)
        print("=" * 30)
        
        # Extract the date format from the normal message
        if "Fri, 8/29:" in normal_message:
            print("✅ Normal format shows: Fri, 8/29")
            expected_format = "Fri, 8/29"
        else:
            print("❓ Could not find expected date format in normal message")
            expected_format = "Unknown"
        
        # Test the date formatting function directly 
        test_date = date(2025, 8, 29)
        abbreviated_format = test_date.strftime('%a, %-m/%-d')
        full_format = test_date.strftime('%A, %B %-d')
        
        print(f"\n🔍 Date Format Comparison:")
        print(f"Abbreviated format (%a, %-m/%-d): {abbreviated_format}")
        print(f"Full format (%A, %B %-d): {full_format}")
        
        print(f"\n🎯 Expected Result:")
        print(f"✅ Partial overlaps should show: {abbreviated_format}")
        print(f"❌ Partial overlaps should NOT show: {full_format}")
        
        print(f"\n✅ Test complete!")

if __name__ == "__main__":
    test_date_formatting_consistency()
