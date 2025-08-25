#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/aaronwalters/Planner_app_live/Planner_v2')

from app import create_app
from app.models.event import Event
from app.models.guest import Guest
from app.models.availability import Availability

def debug_availability_overlap():
    app = create_app()
    
    with app.app_context():
        print("🔍 Debugging Availability Overlap Issues")
        print("=" * 50)
        
        # Find recent event with availability issues
        events = Event.query.order_by(Event.id.desc()).limit(3).all()
        
        for event in events:
            print(f"\n📋 Event {event.id} - Stage: {event.workflow_stage}")
            print(f"Guests: {len(event.guests)}")
            
            # Check guests and their availability
            for guest in event.guests:
                print(f"\n👤 Guest: {guest.name} ({guest.phone_number})")
                print(f"   Availability provided: {guest.availability_provided}")
                print(f"   RSVP status: {guest.rsvp_status}")
                
                # Check availability records
                avail_records = Availability.query.filter_by(guest_id=guest.id).all()
                print(f"   Availability records: {len(avail_records)}")
                
                for i, avail in enumerate(avail_records):
                    print(f"     {i+1}. Date: {avail.date}, Time: {avail.start_time}-{avail.end_time}")
                    print(f"        All day: {avail.all_day}, Event ID: {avail.event_id}")
            
            # Test overlap calculation
            print(f"\n⏰ Testing overlap calculation for Event {event.id}:")
            
            from app.services.availability_service import AvailabilityService
            availability_service = AvailabilityService()
            
            overlaps = availability_service.calculate_availability_overlaps(event.id)
            print(f"Found {len(overlaps)} overlaps:")
            
            for i, overlap in enumerate(overlaps):
                print(f"  {i+1}. Date: {overlap.get('date')}")
                print(f"     Time: {overlap.get('start_time')}-{overlap.get('end_time')}")
                print(f"     Available guests: {overlap.get('available_guests')}")
                print(f"     Guest count: {overlap.get('guest_count')}")

if __name__ == "__main__":
    debug_availability_overlap()
