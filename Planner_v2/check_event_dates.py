#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/aaronwalters/Planner_app_live/Planner_v2')

from app import create_app
from app.models.event import Event
from app.models.guest import Guest
from app.models.availability import Availability

def check_event_dates():
    app = create_app()
    
    with app.app_context():
        print("📅 Checking Event Dates")
        print("=" * 25)
        
        # Find the current active event
        active_event = Event.query.order_by(Event.id.desc()).first()
        print(f"Event ID: {active_event.id}")
        print(f"Workflow Stage: {active_event.workflow_stage}")
        print(f"Start Date: {active_event.start_date}")
        print(f"Selected Date: {getattr(active_event, 'selected_date', 'None')}")
        print(f"Title: {active_event.title}")
        print(f"Location: {active_event.location}")
        print(f"Activity: {active_event.activity}")
        
        # Check what dates were collected during date collection
        print(f"\nWorkflow data:")
        print(f"Available windows: {active_event.available_windows}")
        print(f"Notes: {active_event.notes}")
        
        # Check what availability records exist and their dates
        print(f"\nAvailability records for Event {active_event.id}:")
        availability_records = Availability.query.filter_by(event_id=active_event.id).all()
        
        for record in availability_records:
            guest_name = record.guest.name if record.guest else "Unknown"
            print(f"  {guest_name}: {record.date} ({record.start_time}-{record.end_time})")
        
        # The event should be for Friday Aug 15, 2025 based on screenshots
        # Let's check if we need to update the availability records
        from datetime import date
        expected_date = date(2025, 8, 15)
        print(f"\nExpected event date: {expected_date}")
        
        # Check if there are any records for the wrong date
        wrong_date_records = [r for r in availability_records if r.date != expected_date]
        if wrong_date_records:
            print(f"\nFound {len(wrong_date_records)} records with wrong dates:")
            for record in wrong_date_records:
                guest_name = record.guest.name if record.guest else "Unknown"
                print(f"  {guest_name}: {record.date} (should be {expected_date})")

if __name__ == "__main__":
    check_event_dates()
