#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/aaronwalters/Planner_app_live/Planner_v2')

from app import create_app
from app.models.event import Event
from app.models.guest import Guest
from app.models.availability import Availability

def check_current_database_state():
    app = create_app()
    
    with app.app_context():
        print("🔍 Current Database State Analysis")
        print("=" * 40)
        
        # Check all events
        events = Event.query.all()
        print(f"Total events in database: {len(events)}")
        
        for event in events:
            print(f"\n📋 Event {event.id}: {event.title}")
            print(f"   Stage: {event.workflow_stage}")
            print(f"   Guests: {len(event.guests)}")
            
        # Check orphaned availability records
        print(f"\n🔍 Checking for data integrity issues:")
        
        # 1. Availability records without valid guests
        orphaned_avail = Availability.query.filter(
            ~Availability.guest_id.in_(
                Guest.query.with_entities(Guest.id).subquery()
            )
        ).all()
        print(f"   Orphaned availability records: {len(orphaned_avail)}")
        
        # 2. Availability records pointing to wrong events
        wrong_event_avail = []
        for avail in Availability.query.all():
            if avail.guest and avail.guest.event_id != avail.event_id:
                wrong_event_avail.append(avail)
        print(f"   Wrong-event availability records: {len(wrong_event_avail)}")
        
        # 3. Duplicate availability records
        duplicates = 0
        for guest in Guest.query.all():
            guest_avail = Availability.query.filter_by(guest_id=guest.id).all()
            date_counts = {}
            for avail in guest_avail:
                date_key = (avail.event_id, avail.date.isoformat() if avail.date else None)
                date_counts[date_key] = date_counts.get(date_key, 0) + 1
            
            for date_key, count in date_counts.items():
                if count > 1:
                    duplicates += count - 1
        
        print(f"   Duplicate availability records: {duplicates}")
        
        # 4. Check most recent event for specific issues
        latest_event = Event.query.order_by(Event.id.desc()).first()
        if latest_event:
            print(f"\n📋 Latest Event Analysis ({latest_event.id}):")
            
            all_avail = Availability.query.filter_by(event_id=latest_event.id).all()
            print(f"   Availability records: {len(all_avail)}")
            
            for avail in all_avail:
                guest_name = avail.guest.name if avail.guest else "ORPHANED"
                event_match = "✅" if avail.guest and avail.guest.event_id == avail.event_id else "❌"
                print(f"   {event_match} {guest_name}: {avail.date} {avail.start_time}-{avail.end_time}")
        
        print(f"\n✅ Analysis complete!")

if __name__ == "__main__":
    check_current_database_state()
