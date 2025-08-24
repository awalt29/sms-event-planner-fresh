#!/usr/bin/env python3
"""Test first name extraction functionality"""

from app import create_app
from app.services.message_formatting_service import MessageFormattingService
from app.services.guest_management_service import GuestManagementService

app = create_app()

def test_first_name_extraction():
    """Test the _extract_first_name method"""
    
    with app.app_context():
        print("🧪 Testing First Name Extraction")
        print("=" * 35)
        
        # Test various name formats
        test_cases = [
            ("Aaron Walters", "Aaron"),
            ("John Doe", "John"), 
            ("Mary Jane Smith", "Mary"),
            ("Bob", "Bob"),
            ("", "Friend"),
            (None, "Friend"),
            ("  Sarah  ", "Sarah"),
            ("Jean-Pierre Dupont", "Jean-Pierre"),
            ("Dr. Smith", "Smith"),  # Updated - should skip title
            ("Mike Jr.", "Mike"),
            ("Dr. Emily Watson", "Emily"),  # New test
            ("Mr. John Smith", "John"),  # New test
            ("Mrs. Sarah Johnson", "Sarah"),  # New test
            ("Prof. Michael Brown", "Michael")  # New test
        ]
        
        # Test MessageFormattingService
        message_service = MessageFormattingService()
        
        print("📱 MessageFormattingService Results:")
        print("-" * 30)
        for full_name, expected in test_cases:
            result = message_service._extract_first_name(full_name)
            status = "✅" if result == expected else "❌"
            print(f"{status} '{full_name}' → '{result}' (expected: '{expected}')")
        
        print("\n📧 GuestManagementService Results:")
        print("-" * 30)
        
        # Test GuestManagementService
        guest_service = GuestManagementService()
        for full_name, expected in test_cases:
            result = guest_service._extract_first_name(full_name)
            status = "✅" if result == expected else "❌"
            print(f"{status} '{full_name}' → '{result}' (expected: '{expected}')")
        
        print(f"\n✅ First name extraction test complete!")

if __name__ == "__main__":
    test_first_name_extraction()
