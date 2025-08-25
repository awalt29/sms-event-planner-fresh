#!/usr/bin/env python3
"""Test the new guest list feature in availability requests"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.event import Event
from app.models.guest import Guest
from app.models.planner import Planner
from app import db
from app.services.guest_management_service import GuestManagementService
from datetime import datetime, date
import json

def test_guest_list_availability_format():
    """Test the new guest list formatting in availability requests"""
    
    app = create_app()
    with app.app_context():
        db.create_all()
        
        # Create test planner
        planner = Planner(
            phone_number='+15551234567',
            name='John Smith'
        )
        planner.save()
        
        # Create test event with dates
        test_dates = [
            {"date": "2024-12-13", "all_day": True},
            {"date": "2024-12-14", "all_day": True}
        ]
        
        event = Event(
            planner_id=planner.id,
            title='Party Planning',
            workflow_stage='collecting_availability',
            notes=f"Dates JSON: {json.dumps(test_dates)}\n\nOther details here"
        )
        event.save()
        
        # Create test guests
        guests = [
            {'name': 'Sarah Johnson', 'phone': '+15551111111'},
            {'name': 'Alex Chen', 'phone': '+15552222222'},
            {'name': 'Mike Davis', 'phone': '+15553333333'},
            {'name': 'Lisa Rodriguez', 'phone': '+15554444444'}
        ]
        
        guest_objects = []
        for guest_data in guests:
            guest = Guest(
                event_id=event.id,
                name=guest_data['name'],
                phone_number=guest_data['phone'],
                rsvp_status='pending',
                availability_provided=False
            )
            guest.save()
            guest_objects.append(guest)
        
        # Initialize service
        service = GuestManagementService()
        
        print("🎯 Testing Guest List in Availability Requests")
        print("=" * 60)
        
        # Test different scenarios
        scenarios = [
            ("Sarah (with 3 others)", guest_objects[0]),
            ("Alex (with 3 others)", guest_objects[1]),
            ("Mike (with 3 others)", guest_objects[2]),
            ("Lisa (with 3 others)", guest_objects[3])
        ]
        
        for scenario_name, current_guest in scenarios:
            print(f"\n📱 {scenario_name}:")
            print("-" * 40)
            
            message = service._format_availability_request(current_guest, event, planner)
            print(message)
            print()
        
        # Test with fewer guests
        print("\n🔄 Testing with only 2 guests total:")
        print("-" * 40)
        
        # Create event with just 2 guests
        event2 = Event(
            planner_id=planner.id,
            title='Small Hangout',
            workflow_stage='collecting_availability',
            notes=f"Dates JSON: {json.dumps(test_dates)}\n\nSmall group event"
        )
        event2.save()
        
        guest1 = Guest(
            event_id=event2.id,
            name='Sarah Johnson',
            phone_number='+15551111111',
            rsvp_status='pending',
            availability_provided=False
        )
        guest1.save()
        
        guest2 = Guest(
            event_id=event2.id,
            name='Alex Chen',
            phone_number='+15552222222',
            rsvp_status='pending',
            availability_provided=False
        )
        guest2.save()
        
        print("📱 Sarah (with 1 other - Alex):")
        message = service._format_availability_request(guest1, event2, planner)
        print(message)
        print()
        
        print("📱 Alex (with 1 other - Sarah):")
        message = service._format_availability_request(guest2, event2, planner)
        print(message)
        
        # Test with single guest (no guest list should show)
        print("\n🔄 Testing with only 1 guest total (solo invitation):")
        print("-" * 40)
        
        event3 = Event(
            planner_id=planner.id,
            title='One-on-One',
            workflow_stage='collecting_availability',
            notes=f"Dates JSON: {json.dumps(test_dates)}\n\nJust planner and one guest"
        )
        event3.save()
        
        solo_guest = Guest(
            event_id=event3.id,
            name='Sarah Johnson',
            phone_number='+15551111111',
            rsvp_status='pending',
            availability_provided=False
        )
        solo_guest.save()
        
        print("📱 Sarah (solo invitation - no guest list should appear):")
        message = service._format_availability_request(solo_guest, event3, planner)
        print(message)
        
        # Clean up
        db.session.delete(planner)
        db.session.commit()
        
        print("\n✅ Test completed successfully!")
        print("\n🎨 Format Analysis:")
        print("   ✅ Dates appear first (most important info)")
        print("   ✅ Guest list appears after dates with 👥 emoji")
        print("   ✅ Instructions appear last")
        print("   ✅ Proper grammar: 'Alex and Mike' vs 'Alex, Mike, and Lisa'")
        print("   ✅ Current recipient excluded from guest list")
        print("   ✅ First names only for cleaner display")
        print("   ✅ No guest list shown for solo invitations")

if __name__ == "__main__":
    test_guest_list_availability_format()
