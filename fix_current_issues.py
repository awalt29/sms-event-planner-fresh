#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/aaronwalters/Planner_app_live/Planner_v2')

from app import create_app
from app.models.event import Event
from app.models.guest import Guest
from app.models.availability import Availability

def fix_issues():
    app = create_app()
    
    with app.app_context():
        print("🔧 Fixing Overlap Issues")
        print("=" * 25)
        
        # Find the current active event
        active_event = Event.query.order_by(Event.id.desc()).first()
        
        # 1. Remove John's duplicate availability record
        john = Guest.query.filter_by(name='John', event_id=active_event.id).first()
        if john:
            john_records = Availability.query.filter_by(
                guest_id=john.id,
                event_id=active_event.id,
                date=date(2025, 8, 15)
            ).all()
            
            if len(john_records) > 1:
                print(f"Found {len(john_records)} records for John. Removing duplicates...")
                # Keep the first one, remove the rest
                for record in john_records[1:]:
                    print(f"  Removing duplicate: {record.start_time}-{record.end_time}")
                    record.delete()
                print("✅ Removed John's duplicate records")
        
        # 2. Remove Jude's availability record since he hasn't responded
        jude = Guest.query.filter_by(name='Jude', event_id=active_event.id).first()
        if jude and not jude.availability_provided:
            jude_records = Availability.query.filter_by(
                guest_id=jude.id,
                event_id=active_event.id
            ).all()
            
            if jude_records:
                print(f"Jude hasn't provided availability but has {len(jude_records)} records. Removing...")
                for record in jude_records:
                    print(f"  Removing: {record.date} {record.start_time}-{record.end_time}")
                    record.delete()
                print("✅ Removed Jude's premature availability records")
        
        # Test the fix
        print(f"\n🔍 Testing after fixes:")
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
    from datetime import date
    fix_issues()
