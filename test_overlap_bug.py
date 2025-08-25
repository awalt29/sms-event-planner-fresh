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

def test_screenshot_case():
    app = create_app()
    
    with app.app_context():
        print("� Screenshot Bug Investigation")
        print("=" * 35)
        
        # Create test planner
        test_planner = Planner.query.first()
        if not test_planner:
            test_planner = Planner(phone_number='+1999999999', name='Test Planner')
            test_planner.save()
        
        # Create event
        event = Event(
            planner_id=test_planner.id,
            title='Screenshot Test Event',
            workflow_stage='collecting_availability'
        )
        event.save()
        
        # Create John and Jude exactly as shown in screenshot
        john = Guest(event_id=event.id, name='John', phone_number='+15551001', availability_provided=True)
        john.save()
        jude = Guest(event_id=event.id, name='Jude', phone_number='+15551002', availability_provided=True) 
        jude.save()
        
        print("📅 Creating availability as shown in screenshot:")
        print("-" * 45)
        
        # Jude provided: Fri 8/15: 7pm-11pm, Sat 8/16: 11am to 5pm
        jude_fri = Availability(
            event_id=event.id, guest_id=jude.id, date=date(2025, 8, 15),
            start_time=time(19, 0), end_time=time(23, 0), all_day=False
        )
        jude_fri.save()
        print("✅ Jude Friday: 7pm-11pm")
        
        jude_sat = Availability(
            event_id=event.id, guest_id=jude.id, date=date(2025, 8, 16),
            start_time=time(11, 0), end_time=time(17, 0), all_day=False
        )
        jude_sat.save()
        print("✅ Jude Saturday: 11am-5pm")
        
        # John provided: Fri 8/15:2pm to 6pm, Sat: 8/16: 11am to 11:59pm
        john_fri = Availability(
            event_id=event.id, guest_id=john.id, date=date(2025, 8, 15),
            start_time=time(14, 0), end_time=time(18, 0), all_day=False
        )
        john_fri.save()
        print("✅ John Friday: 2pm-6pm")
        
        john_sat = Availability(
            event_id=event.id, guest_id=john.id, date=date(2025, 8, 16),
            start_time=time(11, 0), end_time=time(23, 59), all_day=False
        )
        john_sat.save()
        print("✅ John Saturday: 11am-11:59pm")
        
        print(f"\n🔍 Database Contents Check:")
        print("-" * 30)
        all_avail = Availability.query.filter_by(event_id=event.id).all()
        for avail in all_avail:
            guest_name = avail.guest.name if avail.guest else "Unknown"
            date_str = avail.date.strftime('%a %m/%d')
            start = avail.start_time.strftime('%I%p').lower() if avail.start_time else "?"
            end = avail.end_time.strftime('%I%p').lower() if avail.end_time else "?"
            print(f"  {guest_name} {date_str}: {start}-{end}")
        
        print(f"\n🧮 Overlap Calculation Results:")
        print("-" * 35)
        
        # Calculate overlaps
        from app.services.availability_service import AvailabilityService
        availability_service = AvailabilityService()
        
        overlaps = availability_service.calculate_availability_overlaps(event.id)
        
        if not overlaps:
            print("❌ No overlaps found!")
        else:
            for i, overlap in enumerate(overlaps, 1):
                date_str = overlap['date'].strftime('%a %m/%d')
                start_time = overlap.get('start_time')
                end_time = overlap.get('end_time')
                guests = overlap.get('available_guests', [])
                guest_count = overlap.get('guest_count', 0)
                print(f"  {i}. {date_str}: {start_time}-{end_time}")
                print(f"     👥 {guest_count} guests: {', '.join(guests)}")
        
        print(f"\n✅ Expected Results:")
        print("-" * 20)
        print("  1. Sat 08/16: 11:00-17:00")
        print("     👥 2 guests: John, Jude")
        print("  (No Friday overlap - times don't overlap!)")
        
        # Cleanup
        for avail in Availability.query.filter_by(event_id=event.id).all():
            avail.delete()
        for guest in Guest.query.filter_by(event_id=event.id).all():
            guest.delete()
        event.delete()
        
        print(f"\n🧹 Test complete!")

if __name__ == "__main__":
    test_screenshot_case()
