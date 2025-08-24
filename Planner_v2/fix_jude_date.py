#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/aaronwalters/Planner_app_live/Planner_v2')

from app import create_app
from app.models.event import Event
from app.models.guest import Guest
from app.models.availability import Availability
from datetime import date

def fix_jude_availability_date():
    app = create_app()
    
    with app.app_context():
        print("🔧 Fixing Jude's availability date")
        print("=" * 35)
        
        # Find the current active event
        active_event = Event.query.order_by(Event.id.desc()).first()
        correct_date = date(2025, 8, 15)  # Friday, August 15, 2025
        
        # Find Jude's availability record with wrong date
        jude = Guest.query.filter_by(name='Jude', event_id=active_event.id).first()
        if jude:
            wrong_record = Availability.query.filter_by(
                guest_id=jude.id,
                event_id=active_event.id,
                date=date(2025, 8, 12)  # Wrong date
            ).first()
            
            if wrong_record:
                print(f"Found Jude's wrong date record: {wrong_record.date}")
                print(f"Updating to correct date: {correct_date}")
                
                wrong_record.date = correct_date
                wrong_record.save()
                
                print("✅ Fixed Jude's availability date")
            else:
                print("No wrong date record found for Jude")
        else:
            print("Jude not found")
        
        # Test overlap calculation again
        print("\n🔍 Testing overlap calculation after date fix:")
        from app.services.availability_service import AvailabilityService
        availability_service = AvailabilityService()
        
        overlaps = availability_service.calculate_availability_overlaps(active_event.id)
        print(f"Found {len(overlaps)} overlaps:")
        
        for i, overlap in enumerate(overlaps):
            date_str = overlap['date'].strftime('%A, %B %-d') if overlap['date'] else 'TBD'
            print(f"  {i+1}. {date_str}: {overlap.get('start_time')}-{overlap.get('end_time')}")
            print(f"     Available guests: {overlap.get('available_guests')}")
            print(f"     Guest count: {overlap.get('guest_count')}")

if __name__ == "__main__":
    fix_jude_availability_date()
