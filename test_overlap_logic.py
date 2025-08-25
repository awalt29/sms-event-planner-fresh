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

def test_overlap_calculation():
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing Overlap Calculation with 5 Guests, 3 Days")
        print("=" * 55)
        
        # Create test planner
        test_planner = Planner.query.first()
        if not test_planner:
            test_planner = Planner(phone_number='+1999999999', name='Test Planner')
            test_planner.save()
        
        # Create test event
        test_event = Event(
            planner_id=test_planner.id,
            title='Test Event',
            workflow_stage='collecting_availability',
            start_date=date(2025, 8, 15)  # Friday
        )
        test_event.save()
        
        # Create 5 test guests
        guests = []
        guest_names = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve']
        
        for i, name in enumerate(guest_names):
            guest = Guest(
                event_id=test_event.id,
                name=name,
                phone_number=f'+155500000{i}',
                rsvp_status='pending',
                availability_provided=True  # All have provided availability
            )
            guest.save()
            guests.append(guest)
        
        # Create availability for 3 days (Friday-Sunday)
        test_dates = [
            date(2025, 8, 15),  # Friday
            date(2025, 8, 16),  # Saturday  
            date(2025, 8, 17)   # Sunday
        ]
        
        # Define different time slots for each guest/day
        availability_data = [
            # Alice - morning person
            {'guest': 'Alice', 'date': test_dates[0], 'start': time(9, 0), 'end': time(14, 0)},   # Fri 9-2
            {'guest': 'Alice', 'date': test_dates[1], 'start': time(8, 0), 'end': time(13, 0)},   # Sat 8-1
            {'guest': 'Alice', 'date': test_dates[2], 'start': time(10, 0), 'end': time(15, 0)},  # Sun 10-3
            
            # Bob - afternoon person
            {'guest': 'Bob', 'date': test_dates[0], 'start': time(12, 0), 'end': time(18, 0)},    # Fri 12-6
            {'guest': 'Bob', 'date': test_dates[1], 'start': time(14, 0), 'end': time(20, 0)},    # Sat 2-8
            {'guest': 'Bob', 'date': test_dates[2], 'start': time(13, 0), 'end': time(19, 0)},    # Sun 1-7
            
            # Charlie - evening person
            {'guest': 'Charlie', 'date': test_dates[0], 'start': time(16, 0), 'end': time(22, 0)}, # Fri 4-10
            {'guest': 'Charlie', 'date': test_dates[1], 'start': time(18, 0), 'end': time(23, 0)}, # Sat 6-11
            {'guest': 'Charlie', 'date': test_dates[2], 'start': time(15, 0), 'end': time(21, 0)}, # Sun 3-9
            
            # Diana - flexible
            {'guest': 'Diana', 'date': test_dates[0], 'start': time(11, 0), 'end': time(17, 0)},   # Fri 11-5
            {'guest': 'Diana', 'date': test_dates[1], 'start': time(10, 0), 'end': time(16, 0)},   # Sat 10-4
            {'guest': 'Diana', 'date': test_dates[2], 'start': time(12, 0), 'end': time(18, 0)},   # Sun 12-6
            
            # Eve - late starter
            {'guest': 'Eve', 'date': test_dates[0], 'start': time(14, 0), 'end': time(20, 0)},     # Fri 2-8
            {'guest': 'Eve', 'date': test_dates[1], 'start': time(15, 0), 'end': time(21, 0)},     # Sat 3-9
            {'guest': 'Eve', 'date': test_dates[2], 'start': time(16, 0), 'end': time(22, 0)},     # Sun 4-10
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
        
        print(f"✅ Created test data:")
        print(f"   Event ID: {test_event.id}")
        print(f"   Guests: {len(guests)} ({', '.join(g.name for g in guests)})")
        print(f"   Dates: {len(test_dates)} (Fri-Sun)")
        print(f"   Availability records: {len(availability_data)}")
        
        # Test the overlap calculation
        print(f"\n⏰ Running overlap calculation...")
        from app.services.availability_service import AvailabilityService
        availability_service = AvailabilityService()
        
        overlaps = availability_service.calculate_availability_overlaps(test_event.id)
        
        print(f"\n📊 Results:")
        print(f"Found {len(overlaps)} overlap periods:")
        
        for i, overlap in enumerate(overlaps, 1):
            date_str = overlap['date'].strftime('%A, %B %-d') if overlap['date'] else 'Unknown'
            print(f"\n{i}. {date_str}")
            print(f"   Time: {overlap.get('start_time', 'N/A')}-{overlap.get('end_time', 'N/A')}")
            print(f"   Available guests: {overlap.get('available_guests', [])}")
            print(f"   Guest count: {overlap.get('guest_count', 0)}")
            
            # Check for duplicates
            guest_list = overlap.get('available_guests', [])
            unique_guests = set(guest_list)
            if len(guest_list) != len(unique_guests):
                print(f"   ❌ DUPLICATE DETECTED: {guest_list}")
            else:
                print(f"   ✅ No duplicates")
        
        # Expected overlaps analysis
        print(f"\n🔍 Expected Overlap Analysis:")
        print(f"Friday: Alice(9-2), Bob(12-6), Charlie(4-10), Diana(11-5), Eve(2-8)")
        print(f"  → Expected overlap: 2-2pm (Alice, Bob, Diana, Eve = 4 guests)")
        print(f"Saturday: Alice(8-1), Bob(2-8), Charlie(6-11), Diana(10-4), Eve(3-9)")
        print(f"  → Expected overlap: None (no common time)")
        print(f"Sunday: Alice(10-3), Bob(1-7), Charlie(3-9), Diana(12-6), Eve(4-10)")
        print(f"  → Expected overlap: 4-3pm (Bob, Charlie, Diana, Eve = 4 guests)")
        
        # Cleanup
        print(f"\n🧹 Cleaning up test data...")
        for avail in Availability.query.filter_by(event_id=test_event.id).all():
            avail.delete()
        for guest in guests:
            guest.delete()
        test_event.delete()
        
        print(f"✅ Test complete!")

if __name__ == "__main__":
    test_overlap_calculation()
