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

def test_new_overlap_logic():
    app = create_app()
    
    with app.app_context():
        print("🧪 Testing New Overlap Logic")
        print("=" * 30)
        print("Rules:")
        print("• 1 guest: Show all their availability")
        print("• 2+ guests: Show overlaps with ≥2 guests and ≥2 hours duration")
        print()
        
        # Create test planner
        test_planner = Planner.query.first()
        if not test_planner:
            test_planner = Planner(phone_number='+1999999999', name='Test Planner')
            test_planner.save()
        
        # Test Case 1: Single guest
        print("📋 Test Case 1: Single Guest")
        print("-" * 30)
        
        event1 = Event(
            planner_id=test_planner.id,
            title='Single Guest Test',
            workflow_stage='collecting_availability'
        )
        event1.save()
        
        alice = Guest(
            event_id=event1.id,
            name='Alice',
            phone_number='+15551001',
            availability_provided=True
        )
        alice.save()
        
        # Alice available 10am-2pm (4 hours)
        avail1 = Availability(
            event_id=event1.id,
            guest_id=alice.id,
            date=date(2025, 8, 15),
            start_time=time(10, 0),
            end_time=time(14, 0),
            all_day=False
        )
        avail1.save()
        
        from app.services.availability_service import AvailabilityService
        availability_service = AvailabilityService()
        
        overlaps1 = availability_service.calculate_availability_overlaps(event1.id)
        print(f"Expected: 1 overlap showing Alice's full availability")
        print(f"Result: {len(overlaps1)} overlaps")
        for overlap in overlaps1:
            print(f"  • {overlap.get('start_time')}-{overlap.get('end_time')} - {overlap.get('available_guests')}")
        
        # Test Case 2: Multiple guests with good overlap
        print(f"\n📋 Test Case 2: Multiple Guests - Good Overlap")
        print("-" * 45)
        
        event2 = Event(
            planner_id=test_planner.id,
            title='Multi Guest Test',
            workflow_stage='collecting_availability'
        )
        event2.save()
        
        # Create 3 guests
        bob = Guest(event_id=event2.id, name='Bob', phone_number='+15551002', availability_provided=True)
        bob.save()
        charlie = Guest(event_id=event2.id, name='Charlie', phone_number='+15551003', availability_provided=True)
        charlie.save()
        diana = Guest(event_id=event2.id, name='Diana', phone_number='+15551004', availability_provided=True)
        diana.save()
        
        # Overlapping availability: Bob(10am-4pm), Charlie(12pm-6pm), Diana(11am-3pm)
        # Expected overlap: 12pm-3pm (3 hours, all 3 guests)
        avail2a = Availability(event_id=event2.id, guest_id=bob.id, date=date(2025, 8, 15), 
                              start_time=time(10, 0), end_time=time(16, 0), all_day=False)
        avail2a.save()
        
        avail2b = Availability(event_id=event2.id, guest_id=charlie.id, date=date(2025, 8, 15),
                              start_time=time(12, 0), end_time=time(18, 0), all_day=False)
        avail2b.save()
        
        avail2c = Availability(event_id=event2.id, guest_id=diana.id, date=date(2025, 8, 15),
                              start_time=time(11, 0), end_time=time(15, 0), all_day=False)
        avail2c.save()
        
        overlaps2 = availability_service.calculate_availability_overlaps(event2.id)
        print(f"Bob: 10am-4pm, Charlie: 12pm-6pm, Diana: 11am-3pm")
        print(f"Expected: Overlap 12pm-3pm (3 hours, all 3 guests)")
        print(f"Result: {len(overlaps2)} overlaps")
        for overlap in overlaps2:
            print(f"  • {overlap.get('start_time')}-{overlap.get('end_time')} - {overlap.get('available_guests')} ({overlap.get('guest_count')} guests)")
        
        # Test Case 3: Short overlap (should be excluded)
        print(f"\n📋 Test Case 3: Short Overlap (< 2 hours)")
        print("-" * 40)
        
        event3 = Event(
            planner_id=test_planner.id,
            title='Short Overlap Test',
            workflow_stage='collecting_availability'
        )
        event3.save()
        
        eve = Guest(event_id=event3.id, name='Eve', phone_number='+15551005', availability_provided=True)
        eve.save()
        frank = Guest(event_id=event3.id, name='Frank', phone_number='+15551006', availability_provided=True)
        frank.save()
        
        # Short overlap: Eve(10am-12pm), Frank(11am-1pm) = 1 hour overlap
        avail3a = Availability(event_id=event3.id, guest_id=eve.id, date=date(2025, 8, 15),
                              start_time=time(10, 0), end_time=time(12, 0), all_day=False)
        avail3a.save()
        
        avail3b = Availability(event_id=event3.id, guest_id=frank.id, date=date(2025, 8, 15),
                              start_time=time(11, 0), end_time=time(13, 0), all_day=False)
        avail3b.save()
        
        overlaps3 = availability_service.calculate_availability_overlaps(event3.id)
        print(f"Eve: 10am-12pm, Frank: 11am-1pm")
        print(f"Expected: No overlaps (only 1 hour overlap, < 2 hours)")
        print(f"Result: {len(overlaps3)} overlaps")
        for overlap in overlaps3:
            print(f"  • {overlap.get('start_time')}-{overlap.get('end_time')} - {overlap.get('available_guests')}")
        
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        for event in [event1, event2, event3]:
            for avail in Availability.query.filter_by(event_id=event.id).all():
                avail.delete()
            for guest in Guest.query.filter_by(event_id=event.id).all():
                guest.delete()
            event.delete()
        
        print(f"✅ Test complete!")

if __name__ == "__main__":
    test_new_overlap_logic()
