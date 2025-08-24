#!/usr/bin/env python3

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.handlers.guest_availability_handler import GuestAvailabilityHandler
from app.services.event_workflow_service import EventWorkflowService
from app.services.guest_management_service import GuestManagementService
from app.services.message_formatting_service import MessageFormattingService
from app.services.ai_processing_service import AIProcessingService
from app import create_app

def test_validation():
    """Test that nonsensical availability entries are rejected"""
    
    app = create_app()
    
    with app.app_context():
        # Initialize services
        event_service = EventWorkflowService()
        guest_service = GuestManagementService()
        message_service = MessageFormattingService()
        ai_service = AIProcessingService()
        
        handler = GuestAvailabilityHandler(event_service, guest_service, message_service, ai_service)
        
        print("Testing availability validation...")
        print("=" * 50)
        
        # Test cases that should be rejected
        invalid_cases = [
            {
                'date': '2025-08-25',
                'start_time': '14:00',
                'end_time': '14:00',  # Same time = zero duration
                'all_day': False
            },
            {
                'date': '2025-08-25', 
                'start_time': '18:00',
                'end_time': '16:00',  # Start after end
                'all_day': False
            },
            {
                'date': '2025-08-25',
                'start_time': '14:00',
                'end_time': '14:15',  # Only 15 minutes (too short)
                'all_day': False
            }
        ]
        
        # Test cases that should be valid
        valid_cases = [
            {
                'date': '2025-08-25',
                'start_time': '14:00', 
                'end_time': '18:00',  # Normal 4-hour slot
                'all_day': False
            },
            {
                'date': '2025-08-25',
                'start_time': '14:00',
                'end_time': '14:30',  # Minimum 30 minutes
                'all_day': False
            }
        ]
        
        print("Testing INVALID cases (should be rejected):")
        for i, case in enumerate(invalid_cases, 1):
            result = handler._validate_availability_entry(case)
            print(f"  {i}. {case['start_time']} to {case['end_time']}")
            if not result['valid']:
                print(f"     ✅ CORRECTLY REJECTED: {result['error']}")
            else:
                print(f"     ❌ WRONGLY ACCEPTED (should be rejected)")
        
        print("\nTesting VALID cases (should be accepted):")
        for i, case in enumerate(valid_cases, 1):
            result = handler._validate_availability_entry(case)
            print(f"  {i}. {case['start_time']} to {case['end_time']}")
            if result['valid']:
                print(f"     ✅ CORRECTLY ACCEPTED")
            else:
                print(f"     ❌ WRONGLY REJECTED: {result['error']}")

if __name__ == "__main__":
    test_validation()
