#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/aaronwalters/Planner_app_live/Planner_v2')

from app import create_app
from app.models.event import Event
from app.models.guest import Guest
from app.models.availability import Availability

def clean_duplicate_availability():
    app = create_app()
    
    with app.app_context():
        print("🧹 Cleaning Duplicate Availability Records")
        print("=" * 45)
        
        latest_event = Event.query.order_by(Event.id.desc()).first()
        print(f"Working on Event {latest_event.id}")
        
        print(f"\n📋 Before cleanup:")
        all_avail = Availability.query.filter_by(event_id=latest_event.id).all()
        for avail in all_avail:
            guest_name = avail.guest.name if avail.guest else "Unknown"
            print(f"   {guest_name}: {avail.date} {avail.start_time}-{avail.end_time}")
        
        # Clean up duplicates - keep the most realistic records
        for guest in latest_event.guests:
            guest_records = Availability.query.filter_by(
                guest_id=guest.id,
                event_id=latest_event.id
            ).all()
            
            if len(guest_records) > 1:
                print(f"\n🔧 Cleaning {guest.name}'s {len(guest_records)} records...")
                
                # Group by date
                date_groups = {}
                for record in guest_records:
                    date_key = record.date.isoformat() if record.date else 'no_date'
                    if date_key not in date_groups:
                        date_groups[date_key] = []
                    date_groups[date_key].append(record)
                
                # For each date, keep the most realistic record
                for date_key, records in date_groups.items():
                    if len(records) > 1:
                        print(f"   {guest.name} on {date_key}: {len(records)} records")
                        
                        # Sort by preference: avoid 23:59 end times, prefer reasonable hours
                        def score_record(r):
                            score = 0
                            # Penalize 23:59 end times (likely wrong)
                            if r.end_time and r.end_time.hour == 23 and r.end_time.minute == 59:
                                score -= 100
                            # Prefer records with reasonable end times
                            if r.end_time and 17 <= r.end_time.hour <= 23:
                                score += 10
                            return score
                        
                        records.sort(key=score_record, reverse=True)
                        keep_record = records[0]
                        
                        print(f"     Keeping: {keep_record.start_time}-{keep_record.end_time}")
                        
                        for record in records[1:]:
                            print(f"     Removing: {record.start_time}-{record.end_time}")
                            record.delete()
        
        print(f"\n📋 After cleanup:")
        all_avail = Availability.query.filter_by(event_id=latest_event.id).all()
        for avail in all_avail:
            guest_name = avail.guest.name if avail.guest else "Unknown"
            print(f"   {guest_name}: {avail.date} {avail.start_time}-{avail.end_time}")
        
        # Test overlap calculation with clean data
        print(f"\n🔍 Testing overlap calculation with clean data:")
        from app.services.availability_service import AvailabilityService
        availability_service = AvailabilityService()
        
        overlaps = availability_service.calculate_availability_overlaps(latest_event.id)
        print(f"Found {len(overlaps)} overlaps:")
        
        for i, overlap in enumerate(overlaps, 1):
            date_str = overlap['date'].strftime('%a %m/%d')
            start_time = overlap.get('start_time')
            end_time = overlap.get('end_time')
            guests = overlap.get('available_guests', [])
            print(f"  {i}. {date_str}: {start_time}-{end_time} - {', '.join(guests)}")
        
        print(f"\n✅ Cleanup complete!")

if __name__ == "__main__":
    clean_duplicate_availability()
