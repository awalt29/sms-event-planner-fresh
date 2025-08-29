#!/usr/bin/env python3
"""Debug script to monitor SMS testing in real-time"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.guest import Guest
from app.models.guest_state import GuestState
from app.models.event import Event
from app.models.availability import Availability

def show_current_state():
    """Show current state of all objects"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("📱 CURRENT SMS APP STATE")
        print("=" * 60)
        
        # Events
        events = Event.query.all()
        print(f"\n🎉 EVENTS ({len(events)}):")
        for event in events:
            planner_name = event.planner.name if event.planner else "Unknown"
            print(f"  • {event.activity or 'No activity'} by {planner_name}")
            print(f"    Status: {event.status}, Stage: {event.workflow_stage}")
            if event.notes:
                if "Dates JSON:" in event.notes:
                    dates_part = event.notes.split("Dates JSON: ")[1].split("\n")[0]
                    print(f"    Dates: {dates_part}")
            print()
        
        # Guests
        guests = Guest.query.all()
        print(f"👥 GUESTS ({len(guests)}):")
        for guest in guests:
            print(f"  • {guest.name} ({guest.phone_number})")
            print(f"    RSVP: {guest.rsvp_status}")
            print(f"    Availability provided: {guest.availability_provided}")
            print(f"    Preferences provided: {guest.preferences_provided}")
            if guest.preferences:
                print(f"    Preferences: {guest.preferences}")
            
            # Show availability
            avail_records = Availability.query.filter_by(guest_id=guest.id).all()
            if avail_records:
                print(f"    Availability:")
                for avail in avail_records:
                    if avail.all_day:
                        print(f"      - {avail.date.strftime('%A')} all day")
                    else:
                        start = avail.start_time.strftime('%I:%M %p').lstrip('0')
                        end = avail.end_time.strftime('%I:%M %p').lstrip('0')
                        print(f"      - {avail.date.strftime('%A')} {start}-{end}")
            print()
        
        # Guest States
        states = GuestState.query.all()
        print(f"📱 GUEST STATES ({len(states)}):")
        for state in states:
            print(f"  • {state.phone_number}: {state.current_state}")
            if state.state_data:
                print(f"    Data: {state.get_state_data()}")
            print()
        
        if not events and not guests and not states:
            print("📭 No data found. Start testing by creating an event!")

if __name__ == '__main__':
    show_current_state()
