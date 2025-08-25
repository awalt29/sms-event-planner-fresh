#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/aaronwalters/Planner_app_live/Planner_v2')

from app import create_app
from app.models.event import Event
from app.models.guest import Guest
from app.models.availability import Availability
from app.models.planner import Planner
from datetime import date, time

def test_current_logic():
    app = create_app()
    
    with app.app_context():
        print("🔍 Testing Current Overlap Logic (ALL guests must be available)")
        print("=" * 65)
        
        # Create test planner
        test_planner = Planner.query.first()
        if not test_planner:
            test_planner = Planner(phone_number='+1999999999', name='Test Planner')
            test_planner.save()
        
        # Create test event
        test_event = Event(
            planner_id=test_planner.id,
            title='Test Event 2',
            workflow_stage='collecting_availability',
            start_date=date(2025, 8, 15)
        )
        test_event.save()
        
        # Create 3 test guests with overlapping availability
        guests = []
        guest_names = ['Alice', 'Bob', 'Charlie']
        
        for i, name in enumerate(guest_names):
            guest = Guest(
                event_id=test_event.id,
                name=name,
                phone_number=f'+155500010{i}',
                rsvp_status='pending',
                availability_provided=True
            )
            guest.save()
            guests.append(guest)
        
        # Create availability with clear overlaps
        test_date = date(2025, 8, 15)  # Friday
        
        availability_data = [
            # All available 2-4pm
            {'guest': 'Alice', 'date': test_date, 'start': time(10, 0), 'end': time(16, 0)},  # 10am-4pm
            {'guest': 'Bob', 'date': test_date, 'start': time(14, 0), 'end': time(18, 0)},    # 2pm-6pm  
            {'guest': 'Charlie', 'date': test_date, 'start': time(12, 0), 'end': time(20, 0)}, # 12pm-8pm
        ]
        
        # Create availability records
        for avail in availability_data:
            guest = next(g for g in guests if g.name == avail['guest'])
            availability = Availability(
                event_id=test_event.id,
                guest_id=guest.id,
                date=avail['date'],
                start_time=avail['start'],
                end_time=avail['end'],
                all_day=False
            )
            availability.save()
        
        print(f"✅ Created test scenario:")
        print(f"   Alice: 10am-4pm")
        print(f"   Bob: 2pm-6pm")  
        print(f"   Charlie: 12pm-8pm")
        print(f"   Expected ALL-available overlap: 2pm-4pm (when all 3 are free)")
        
        # Test the overlap calculation
        print(f"\n⏰ Running overlap calculation...")
        from app.services.availability_service import AvailabilityService
        availability_service = AvailabilityService()
        
        overlaps = availability_service.calculate_availability_overlaps(test_event.id)
        
        print(f"\n📊 Results:")
        if overlaps:
            for i, overlap in enumerate(overlaps, 1):
                date_str = overlap['date'].strftime('%A, %B %-d') if overlap['date'] else 'Unknown'
                print(f"{i}. {date_str}")
                print(f"   Time: {overlap.get('start_time', 'N/A')}-{overlap.get('end_time', 'N/A')}")
                print(f"   Available guests: {overlap.get('available_guests', [])}")
                print(f"   Guest count: {overlap.get('guest_count', 0)}")
        else:
            print("   No overlaps found")
        
        # Manual calculation
        print(f"\n🧮 Manual calculation:")
        print(f"   Latest start time: 2pm (Bob)")
        print(f"   Earliest end time: 4pm (Alice)")
        print(f"   2pm < 4pm = {time(14,0) < time(16,0)} → Should find overlap!")
        
        # Debug the calculation step by step
        print(f"\n🔍 Debug the calculation:")
        availabilities = Availability.query.join(Guest).filter(
            Availability.event_id == test_event.id,
            Guest.availability_provided == True
        ).all()
        
        print(f"   Found {len(availabilities)} availability records:")
        for avail in availabilities:
            print(f"     {avail.guest.name}: {avail.start_time}-{avail.end_time}")
        
        # Test the _calculate_time_overlap method directly
        guest_data = []
        for avail in availabilities:
            guest_data.append({
                'guest_id': avail.guest_id,
                'guest_name': avail.guest.name,
                'start_time': avail.start_time,
                'end_time': avail.end_time,
                'all_day': avail.all_day
            })
        
        print(f"\n   Testing _calculate_time_overlap directly:")
        direct_result = availability_service._calculate_time_overlap(guest_data)
        print(f"   Direct result: {direct_result}")
        
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        for avail in Availability.query.filter_by(event_id=test_event.id).all():
            avail.delete()
        for guest in guests:
            guest.delete()
        test_event.delete()
        
        print(f"✅ Test complete!")

if __name__ == "__main__":
    test_current_logic()
