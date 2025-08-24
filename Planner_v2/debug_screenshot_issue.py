#!/usr/bin/env python3
"""Debug the exact scenario from the screenshots"""

from app import create_app
from app.models.event import Event
from app.models.planner import Planner
from app.models.guest import Guest
from app.models.availability import Availability
from app.services.availability_service import AvailabilityService
from datetime import date, time as dt_time

app = create_app()

def debug_screenshot_scenario():
    """Recreate the exact scenario from screenshots"""
    with app.app_context():
        print("🧪 Debugging Screenshot Scenario")
        print("=" * 50)
        
        # Clean up existing test data
        test_planner = Planner.query.filter_by(phone_number='+19999999999').first()
        if test_planner:
            for event in test_planner.events:
                for guest in event.guests:
                    for avail in guest.availability_records:
                        avail.delete()
                    guest.delete()
                event.delete()
            test_planner.delete()
        
        # Create test planner (Jude)
        planner = Planner(phone_number='+19999999999', name='Jude')
        planner.save()
        
        # Create test event 
        event = Event(
            planner_id=planner.id,
            title='Hangout Event',
            workflow_stage='overlap_review',
            start_date=date(2025, 8, 30)  # Saturday
        )
        event.save()
        
        # Create guests
        aaron = Guest(
            event_id=event.id,
            name='Aaron',
            phone_number='+15555551111', 
            availability_provided=True,
            rsvp_status='pending'
        )
        aaron.save()
        
        aaron_ron = Guest(
            event_id=event.id,
            name='A A Ron',
            phone_number='+15555552222',
            availability_provided=True, 
            rsvp_status='pending'
        )
        aaron_ron.save()
        
        print(f"✅ Created event {event.id} with guests:")
        print(f"   - {aaron.name} ({aaron.phone_number})")
        print(f"   - {aaron_ron.name} ({aaron_ron.phone_number})")
        
        # Create availability from screenshots
        # Aaron: "Saturday after 12pm, Sunday all day"
        aaron_sat = Availability(
            event_id=event.id,
            guest_id=aaron.id,
            date=date(2025, 8, 30),  # Saturday
            start_time=dt_time(12, 0),  # 12pm
            end_time=dt_time(23, 59),   # 11:59pm
            all_day=False
        )
        aaron_sat.save()
        
        aaron_sun = Availability(
            event_id=event.id,
            guest_id=aaron.id,
            date=date(2025, 8, 31),  # Sunday
            start_time=dt_time(8, 0),   # 8am (system default for "all day")
            end_time=dt_time(23, 59),   # 11:59pm
            all_day=True  # This was marked as "all day"
        )
        aaron_sun.save()
        
        # A A Ron: "Saturday after 4pm, Sunday all day, Monday 5p-9p"
        aaron_ron_sat = Availability(
            event_id=event.id,
            guest_id=aaron_ron.id,
            date=date(2025, 8, 30),  # Saturday
            start_time=dt_time(16, 0),  # 4pm
            end_time=dt_time(23, 59),   # 11:59pm  
            all_day=False
        )
        aaron_ron_sat.save()
        
        aaron_ron_sun = Availability(
            event_id=event.id,
            guest_id=aaron_ron.id,
            date=date(2025, 8, 31),  # Sunday
            start_time=dt_time(8, 0),   # 8am
            end_time=dt_time(23, 59),   # 11:59pm
            all_day=True  # This was marked as "all day"
        )
        aaron_ron_sun.save()
        
        aaron_ron_mon = Availability(
            event_id=event.id,
            guest_id=aaron_ron.id,
            date=date(2025, 9, 1),   # Monday
            start_time=dt_time(17, 0),  # 5pm
            end_time=dt_time(21, 0),    # 9pm
            all_day=False
        )
        aaron_ron_mon.save()
        
        print(f"\n📅 Created availability records:")
        print(f"Aaron:")
        print(f"  - Sat 8/30: 12:00-23:59 (all_day=False)")
        print(f"  - Sun 8/31: 08:00-23:59 (all_day=True)")
        print(f"A A Ron:")
        print(f"  - Sat 8/30: 16:00-23:59 (all_day=False)")
        print(f"  - Sun 8/31: 08:00-23:59 (all_day=True)")
        print(f"  - Mon 9/1:  17:00-21:00 (all_day=False)")
        
        # Calculate overlaps
        print(f"\n⏰ Running overlap calculation...")
        availability_service = AvailabilityService()
        overlaps = availability_service.calculate_availability_overlaps(event.id)
        
        print(f"\n📊 Overlap Results:")
        print(f"Found {len(overlaps)} overlaps:")
        
        for i, overlap in enumerate(overlaps, 1):
            date_str = overlap['date'].strftime('%A, %B %-d') if overlap['date'] else 'Unknown'
            print(f"\n{i}. {date_str}: {overlap.get('start_time')}-{overlap.get('end_time')}")
            print(f"   Attendance: {overlap.get('guest_count')}/{len([aaron, aaron_ron])} responded")
            print(f"   Available: {', '.join(overlap.get('available_guests', []))}")
        
        print(f"\n🔍 Expected vs Actual:")
        print(f"Expected overlaps:")
        print(f"1. Saturday, August 30: 16:00-23:59 (Aaron 12pm+, A A Ron 4pm+)")
        print(f"2. Sunday, August 31: 08:00-23:59 (both all day)")
        print(f"Expected NO Monday overlap (Aaron not available)")
        
        # Debug by examining each date separately
        print(f"\n🔬 Debug date-by-date calculation:")
        
        # Get availability by date (imports already done at top)
        
        availabilities = Availability.query.join(Guest).filter(
            Availability.event_id == event.id,
            Guest.availability_provided == True
        ).all()
        
        # Group by date
        date_groups = {}
        for avail in availabilities:
            date_key = avail.date.isoformat()
            if date_key not in date_groups:
                date_groups[date_key] = []
            date_groups[date_key].append(avail)
        
        for date_key, avails in sorted(date_groups.items()):
            print(f"\n📅 Date: {date_key}")
            guest_data = []
            for avail in avails:
                guest_info = {
                    'guest_id': avail.guest_id,
                    'guest_name': avail.guest.name,
                    'start_time': avail.start_time,
                    'end_time': avail.end_time,
                    'all_day': avail.all_day
                }
                guest_data.append(guest_info)
                print(f"  {avail.guest.name}: {avail.start_time}-{avail.end_time} (all_day={avail.all_day})")
            
            # Calculate overlap for this date
            date_overlaps = availability_service._calculate_time_overlap(guest_data)
            print(f"  → Calculated overlaps: {len(date_overlaps)}")
            for j, overlap in enumerate(date_overlaps):
                print(f"    {j+1}. {overlap.get('start_time')}-{overlap.get('end_time')} (guests: {overlap.get('available_guests', [])})")
        
        # Cleanup
        print(f"\n🧹 Cleaning up...")
        for avail in [aaron_sat, aaron_sun, aaron_ron_sat, aaron_ron_sun, aaron_ron_mon]:
            avail.delete()
        aaron.delete()
        aaron_ron.delete()
        event.delete()
        planner.delete()
        
        print(f"✅ Debug complete!")

if __name__ == "__main__":
    debug_screenshot_scenario()
