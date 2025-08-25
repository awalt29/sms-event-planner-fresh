#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/aaronwalters/Planner_app_live/Planner_v2')

from app import create_app
from app.models.event import Event
from app.models.guest import Guest
from app.models.availability import Availability

def fix_duplicate_availability():
    app = create_app()
    
    with app.app_context():
        print("🔧 Fixing Duplicate Availability Records")
        print("=" * 40)
        
        # Find the current active event
        active_event = Event.query.order_by(Event.id.desc()).first()
        print(f"Active Event ID: {active_event.id}")
        
        # Clean up availability records that don't belong to this event
        print("\n1. Cleaning up wrong-event availability records...")
        wrong_event_records = Availability.query.filter(
            Availability.event_id != active_event.id
        ).all()
        
        print(f"Found {len(wrong_event_records)} records from other events")
        for record in wrong_event_records:
            guest_name = record.guest.name if record.guest else "Unknown"
            print(f"   Removing: {guest_name} - Event {record.event_id}, Date {record.date}")
            record.delete()
        
        # Clean up duplicate records for the same guest/event/date
        print("\n2. Cleaning up duplicate records for same guest/event/date...")
        
        for guest in active_event.guests:
            # Get all availability records for this guest and event
            guest_records = Availability.query.filter_by(
                guest_id=guest.id,
                event_id=active_event.id
            ).all()
            
            if len(guest_records) > 1:
                print(f"   Guest {guest.name} has {len(guest_records)} records")
                
                # Group by date
                date_groups = {}
                for record in guest_records:
                    date_key = record.date.isoformat() if record.date else 'no_date'
                    if date_key not in date_groups:
                        date_groups[date_key] = []
                    date_groups[date_key].append(record)
                
                # Keep only the most recent record for each date
                for date_key, records in date_groups.items():
                    if len(records) > 1:
                        # Sort by ID (assuming higher ID = more recent)
                        records.sort(key=lambda x: x.id)
                        keep_record = records[-1]  # Keep the last (most recent)
                        
                        for record in records[:-1]:  # Delete all but the last
                            print(f"     Removing duplicate: Date {record.date}, Time {record.start_time}-{record.end_time}")
                            record.delete()
        
        print("\n3. Final cleanup - orphaned records...")
        # Clean up any orphaned availability records
        from app.services.availability_service import AvailabilityService
        availability_service = AvailabilityService()
        cleaned_count = availability_service.cleanup_orphaned_availability_records(active_event.id)
        print(f"   Cleaned up {cleaned_count} orphaned records")
        
        print("\n✅ Cleanup complete!")
        
        # Test the overlap calculation again
        print("\n🔍 Testing overlap calculation after cleanup:")
        overlaps = availability_service.calculate_availability_overlaps(active_event.id)
        print(f"Found {len(overlaps)} overlaps:")
        
        for i, overlap in enumerate(overlaps):
            print(f"  {i+1}. Date: {overlap.get('date')}")
            print(f"     Time: {overlap.get('start_time')}-{overlap.get('end_time')}")
            print(f"     Available guests: {overlap.get('available_guests')}")
            print(f"     Guest count: {overlap.get('guest_count')}")

if __name__ == "__main__":
    fix_duplicate_availability()
