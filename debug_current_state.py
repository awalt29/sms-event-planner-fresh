#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/aaronwalters/Planner_app_live/Planner_v2')

from app import create_app
from app.models.event import Event
from app.models.guest import Guest
from app.models.availability import Availability

def debug_current_state():
    app = create_app()
    
    with app.app_context():
        print("🔍 Current State Debug")
        print("=" * 25)
        
        # Find the current active event
        active_event = Event.query.order_by(Event.id.desc()).first()
        print(f"Event ID: {active_event.id}")
        
        print(f"\n👥 Guest Status:")
        for guest in active_event.guests:
            print(f"  {guest.name}: availability_provided = {guest.availability_provided}")
            print(f"    Phone: {guest.phone_number}")
            print(f"    RSVP: {guest.rsvp_status}")
        
        print(f"\n📅 Availability Records:")
        availability_records = Availability.query.filter_by(event_id=active_event.id).all()
        print(f"Total records: {len(availability_records)}")
        
        for record in availability_records:
            guest_name = record.guest.name if record.guest else "Unknown"
            print(f"  {guest_name} (ID: {record.guest_id}): {record.date} {record.start_time}-{record.end_time}")
        
        # Check for duplicates
        guest_date_counts = {}
        for record in availability_records:
            if record.guest:
                key = f"{record.guest.name}_{record.date}"
                guest_date_counts[key] = guest_date_counts.get(key, 0) + 1
        
        print(f"\n🔍 Duplicate Check:")
        for key, count in guest_date_counts.items():
            if count > 1:
                print(f"  ❌ {key}: {count} records (DUPLICATE!)")
            else:
                print(f"  ✅ {key}: {count} record")
        
        # Test overlap calculation
        print(f"\n⏰ Overlap Calculation Test:")
        from app.services.availability_service import AvailabilityService
        availability_service = AvailabilityService()
        
        overlaps = availability_service.calculate_availability_overlaps(active_event.id)
        print(f"Found {len(overlaps)} overlaps:")
        
        for i, overlap in enumerate(overlaps):
            print(f"  {i+1}. Date: {overlap.get('date')}")
            print(f"     Available guests: {overlap.get('available_guests')}")
            print(f"     Guest count: {overlap.get('guest_count')}")
            print(f"     Time: {overlap.get('start_time')}-{overlap.get('end_time')}")

if __name__ == "__main__":
    debug_current_state()
