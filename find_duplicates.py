#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/aaronwalters/Planner_app_live/Planner_v2')

from app import create_app
from app.models.event import Event
from app.models.guest import Guest
from app.models.availability import Availability

def find_and_fix_duplicates():
    app = create_app()
    
    with app.app_context():
        print("🔍 Finding Remaining Duplicates")
        print("=" * 32)
        
        # Find the current active event
        active_event = Event.query.order_by(Event.id.desc()).first()
        print(f"Event ID: {active_event.id}")
        
        # Get all availability records for this event
        records = Availability.query.filter_by(event_id=active_event.id).all()
        print(f"Total availability records: {len(records)}")
        
        # Show all records with details
        print(f"\nAll availability records:")
        for i, record in enumerate(records):
            guest_name = record.guest.name if record.guest else "Unknown"
            print(f"  {i+1}. ID: {record.id}, Guest: {guest_name} (GuestID: {record.guest_id})")
            print(f"     Date: {record.date}, Time: {record.start_time}-{record.end_time}")
            print(f"     Guest availability_provided: {record.guest.availability_provided if record.guest else 'N/A'}")
        
        # Look for exact duplicates
        print(f"\n🔍 Checking for exact duplicates:")
        seen_combinations = {}
        duplicates_to_remove = []
        
        for record in records:
            # Create a key for guest_id + date + start_time + end_time
            key = f"{record.guest_id}_{record.date}_{record.start_time}_{record.end_time}"
            
            if key in seen_combinations:
                print(f"❌ DUPLICATE FOUND: {record.guest.name if record.guest else 'Unknown'}")
                print(f"   Record ID: {record.id} (duplicate of ID: {seen_combinations[key]})")
                duplicates_to_remove.append(record)
            else:
                seen_combinations[key] = record.id
                print(f"✅ Unique: {record.guest.name if record.guest else 'Unknown'} - Record ID: {record.id}")
        
        # Remove duplicates
        if duplicates_to_remove:
            print(f"\n🗑️ Removing {len(duplicates_to_remove)} duplicate records:")
            for record in duplicates_to_remove:
                guest_name = record.guest.name if record.guest else "Unknown"
                print(f"   Removing: {guest_name} - Record ID: {record.id}")
                record.delete()
            print("✅ Duplicates removed!")
        else:
            print(f"\n✅ No duplicates found!")
        
        # Test overlap calculation after cleanup
        print(f"\n🔍 Testing overlap calculation after cleanup:")
        from app.services.availability_service import AvailabilityService
        availability_service = AvailabilityService()
        
        overlaps = availability_service.calculate_availability_overlaps(active_event.id)
        print(f"Found {len(overlaps)} overlaps:")
        
        for i, overlap in enumerate(overlaps):
            print(f"  {i+1}. Date: {overlap.get('date')}")
            print(f"     Available guests: {overlap.get('available_guests')}")
            print(f"     Guest count: {overlap.get('guest_count')}")

if __name__ == "__main__":
    find_and_fix_duplicates()
