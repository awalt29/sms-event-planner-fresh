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

def test_comprehensive_six_guests():
    app = create_app()
    
    with app.app_context():
        print("🧪 Comprehensive 6-Guest Overlap Test")
        print("=" * 40)
        
        # Create test planner
        test_planner = Planner.query.first()
        if not test_planner:
            test_planner = Planner(phone_number='+1999999999', name='Test Planner')
            test_planner.save()
        
        # Create event
        event = Event(
            planner_id=test_planner.id,
            title='Comprehensive Six Guest Test',
            workflow_stage='collecting_availability'
        )
        event.save()
        
        # Create 6 guests
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
        
        # Availability pattern:
        # Alice:   9am-5pm   (8 hours)
        # Bob:     10am-4pm  (6 hours) 
        # Charlie: 11am-3pm  (4 hours)
        # Diana:   12pm-6pm  (6 hours)
        # Eve:     1pm-7pm   (6 hours)
        # Frank:   2pm-4pm   (2 hours)
        
        availability_data = [
            ('Alice', time(9, 0), time(17, 0)),
            ('Bob', time(10, 0), time(16, 0)),
            ('Charlie', time(11, 0), time(15, 0)),
            ('Diana', time(12, 0), time(18, 0)),
            ('Eve', time(13, 0), time(19, 0)),
            ('Frank', time(14, 0), time(16, 0)),
        ]
        
        for i, (name, start, end) in enumerate(availability_data):
            avail = Availability(
                event_id=event.id,
                guest_id=guests[i].id,
                date=date(2025, 8, 15),
                start_time=start,
                end_time=end,
                all_day=False
            )
            avail.save()
            print(f"  {name:8}: {start.strftime('%I%p').lower()}-{end.strftime('%I%p').lower()}")
        
        print()
        
        # Calculate overlaps
        from app.services.availability_service import AvailabilityService
        availability_service = AvailabilityService()
        
        overlaps = availability_service.calculate_availability_overlaps(event.id)
        
        print(f"🔍 All Valid Overlaps (≥2 hours, ≥2 guests):")
        print("-" * 45)
        
        for i, overlap in enumerate(overlaps, 1):
            start_time = overlap.get('start_time')
            end_time = overlap.get('end_time')
            guest_list = overlap.get('available_guests', [])
            guest_count = overlap.get('guest_count', 0)
            
            # Calculate duration
            start_hour, start_min = map(int, start_time.split(':'))
            end_hour, end_min = map(int, end_time.split(':'))
            duration_hours = (end_hour + end_min/60) - (start_hour + start_min/60)
            
            print(f"  {i:2d}. {start_time}-{end_time} ({duration_hours:.1f}h)")
            print(f"      👥 {guest_count} guests: {', '.join(guest_list)}")
            print()
        
        print("✨ Key Expected Windows Analysis:")
        print("-" * 35)
        
        expected_windows = [
            ("10am-3pm", "Alice, Bob, Charlie", 5.0),
            ("11am-3pm", "Alice, Bob, Charlie", 4.0),
            ("12pm-3pm", "Alice, Bob, Charlie, Diana", 3.0),
            ("1pm-3pm", "Alice, Bob, Charlie, Diana, Eve", 2.0),
            ("1pm-4pm", "Alice, Bob, Diana, Eve", 3.0),
            ("2pm-4pm", "Alice, Bob, Diana, Eve, Frank", 2.0),
        ]
        
        for window, guests_str, hours in expected_windows:
            print(f"  • {window} ({hours}h): {guests_str}")
        
        print(f"\n📊 Summary:")
        print(f"  Found: {len(overlaps)} overlaps")
        print(f"  Expected: {len(expected_windows)} major overlapping windows")
        
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        for avail in Availability.query.filter_by(event_id=event.id).all():
            avail.delete()
        for guest in Guest.query.filter_by(event_id=event.id).all():
            guest.delete()
        event.delete()
        
        print("✅ Comprehensive test complete!")

if __name__ == "__main__":
    test_comprehensive_six_guests()
