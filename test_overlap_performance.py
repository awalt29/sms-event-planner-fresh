#!/usr/bin/env python3
"""Test overlap detection performance after optimization"""

import time
from app import create_app
from app.services.availability_service import AvailabilityService
from app.models.event import Event
from app.models.planner import Planner
from app.models.guest import Guest
from app.models.availability import Availability
from datetime import date, time as dt_time

app = create_app()

def test_overlap_performance():
    """Test performance of overlap calculation"""
    with app.app_context():
        print("=== Testing Overlap Detection Performance ===\n")
        
        # Clean up any existing test data
        test_planner = Planner.query.filter_by(phone_number="+19999999999").first()
        if test_planner:
            for event in test_planner.events:
                for guest in event.guests:
                    for avail in guest.availability_records:
                        avail.delete()
                    guest.delete()
                event.delete()
            test_planner.delete()
        
        # Create test data
        test_planner = Planner(phone_number="+19999999999", name="Performance Test")
        test_planner.save()
        
        test_event = Event(
            planner_id=test_planner.id,
            workflow_stage='collecting_availability',
            notes="Performance test event"
        )
        test_event.save()
        
        # Create multiple guests with availability
        guests = []
        for i in range(10):  # 10 guests
            guest = Guest(
                event_id=test_event.id, 
                name=f"Guest {i+1}", 
                phone_number=f"+1555000000{i}", 
                availability_provided=True
            )
            guest.save()
            guests.append(guest)
        
        # Create overlapping availability for multiple dates
        test_dates = [
            date(2025, 8, 16),  # Saturday
            date(2025, 8, 17),  # Sunday
            date(2025, 8, 23),  # Next Saturday
        ]
        
        for test_date in test_dates:
            for guest in guests:
                # Each guest available at slightly different times
                start_hour = 10 + (guest.id % 6)  # 10am to 4pm starts
                end_hour = start_hour + 4  # 4 hour windows
                
                availability = Availability(
                    guest_id=guest.id,
                    event_id=test_event.id,
                    date=test_date,
                    start_time=dt_time(start_hour, 0),
                    end_time=dt_time(end_hour, 0),
                    all_day=False
                )
                availability.save()
        
        # Test performance
        service = AvailabilityService()
        
        # Warm up
        service.calculate_availability_overlaps(test_event.id)
        
        # Time multiple runs
        times = []
        for i in range(10):
            start_time = time.time()
            overlaps = service.calculate_availability_overlaps(test_event.id)
            end_time = time.time()
            
            duration = end_time - start_time
            times.append(duration)
            print(f"Run {i+1}: {duration:.4f}s - Found {len(overlaps)} overlaps")
        
        # Calculate stats
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        
        print(f"\nPerformance Results:")
        print(f"Average: {avg_time:.4f}s")
        print(f"Min: {min_time:.4f}s") 
        print(f"Max: {max_time:.4f}s")
        
        if avg_time < 0.1:
            print("✅ EXCELLENT: Sub-100ms performance")
        elif avg_time < 0.5:
            print("✅ GOOD: Sub-500ms performance") 
        elif avg_time < 1.0:
            print("⚠️  OK: Sub-1s performance")
        else:
            print("❌ SLOW: Over 1s - needs more optimization")
        
        # Show sample results
        print(f"\nSample overlaps found:")
        for i, overlap in enumerate(overlaps[:3]):
            date_str = overlap['date'].strftime('%a %m/%d')
            print(f"{i+1}. {date_str}: {overlap['start_time']}-{overlap['end_time']} ({overlap['guest_count']} guests)")
        
        # Cleanup
        for guest in guests:
            for avail in guest.availability_records:
                avail.delete()
            guest.delete()
        test_event.delete()
        test_planner.delete()

if __name__ == "__main__":
    test_overlap_performance()
