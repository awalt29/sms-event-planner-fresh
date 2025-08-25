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

def test_six_guests():
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Overlap Logic with 6 Guests")
        print("=" * 40)
        print("Rules: Show overlaps with ≥2 guests and ≥2 hours duration")
        print()
        
        # Create test planner
        test_planner = Planner.query.first()
        if not test_planner:
            test_planner = Planner(phone_number='+1999999999', name='Test Planner')
            test_planner.save()
        
        # Create event
        event = Event(
            planner_id=test_planner.id,
            title='Six Guest Test Event',
            workflow_stage='collecting_availability'
        )
        event.save()
        
        # Create 6 guests with different availability patterns
        guests = []
        guest_names = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank']
        
        for i, name in enumerate(guest_names):
            guest = Guest(
                event_id=event.id,
                name=name,
                phone_number=f'+155510{i+10:02d}',
                availability_provided=True
            )
            guest.save()
            guests.append(guest)
        
        print("📅 Guest Availability Schedule:")
        print("-" * 30)
        
        # Complex availability pattern:
        # Alice:   9am-5pm   (8 hours)
        # Bob:     10am-4pm  (6 hours) 
        # Charlie: 11am-3pm  (4 hours)
        # Diana:   12pm-6pm  (6 hours)
        # Eve:     1pm-7pm   (6 hours)
        # Frank:   2pm-4pm   (2 hours)
        
        availability_data = [
            (guests[0], time(9, 0), time(17, 0)),   # Alice: 9am-5pm
            (guests[1], time(10, 0), time(16, 0)),  # Bob: 10am-4pm
            (guests[2], time(11, 0), time(15, 0)),  # Charlie: 11am-3pm
            (guests[3], time(12, 0), time(18, 0)),  # Diana: 12pm-6pm
            (guests[4], time(13, 0), time(19, 0)),  # Eve: 1pm-7pm
            (guests[5], time(14, 0), time(16, 0)),  # Frank: 2pm-4pm
        ]
        
        for guest, start, end in availability_data:
            avail = Availability(
                event_id=event.id,
                guest_id=guest.id,
                date=date(2025, 8, 15),
                start_time=start,
                end_time=end,
                all_day=False
            )
            avail.save()
            print(f"  {guest.name:8}: {start.strftime('%I%p').lower()}-{end.strftime('%I%p').lower()}")
        
        print()
        
        # Calculate overlaps
        from app.services.availability_service import AvailabilityService
        availability_service = AvailabilityService()
        
        overlaps = availability_service.calculate_availability_overlaps(event.id)
        
        print(f"🔍 Overlap Analysis Results:")
        print("-" * 30)
        print(f"Found {len(overlaps)} valid overlaps (≥2 hours, ≥2 guests):")
        print()
        
        for i, overlap in enumerate(overlaps, 1):
            start_time = overlap.get('start_time')
            end_time = overlap.get('end_time')
            guest_list = overlap.get('available_guests', [])
            guest_count = overlap.get('guest_count', 0)
            
            # Calculate duration
            if isinstance(start_time, str) and isinstance(end_time, str):
                start_hour = int(start_time.split(':')[0])
                start_min = int(start_time.split(':')[1])
                end_hour = int(end_time.split(':')[0])
                end_min = int(end_time.split(':')[1])
                duration_hours = (end_hour + end_min/60) - (start_hour + start_min/60)
            else:
                duration_hours = 0
            
            print(f"  {i}. {start_time}-{end_time} ({duration_hours:.1f} hours)")
            print(f"     👥 {guest_count} guests: {', '.join(guest_list)}")
            print()
        
        print("📊 Expected Overlaps Analysis:")
        print("-" * 30)
        print("Key overlapping windows that should appear:")
        print("• 10am-3pm (5 hours): Alice, Bob, Charlie")
        print("• 12pm-3pm (3 hours): Alice, Bob, Charlie, Diana") 
        print("• 1pm-3pm (2 hours): Alice, Bob, Charlie, Diana, Eve")
        print("• 2pm-3pm (1 hour): All 6 guests - BUT excluded (< 2 hours)")
        print("• 1pm-4pm (3 hours): Alice, Bob, Diana, Eve")
        print("• 2pm-4pm (2 hours): Alice, Bob, Diana, Eve, Frank")
        print()
        
        # Cleanup
        print("🧹 Cleaning up...")
        for avail in Availability.query.filter_by(event_id=event.id).all():
            avail.delete()
        for guest in Guest.query.filter_by(event_id=event.id).all():
            guest.delete()
        event.delete()
        
        print("✅ Six guest test complete!")

if __name__ == "__main__":
    test_six_guests()
