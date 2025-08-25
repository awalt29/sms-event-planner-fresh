#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/aaronwalters/Planner_app_live/Planner_v2')

from app import create_app
from app.models.event import Event

def check_guest_status():
    app = create_app()
    
    with app.app_context():
        print("👥 Checking Guest Status")
        print("=" * 25)
        
        # Find the current active event
        active_event = Event.query.order_by(Event.id.desc()).first()
        
        total_guests = len(active_event.guests)
        responded_count = sum(1 for guest in active_event.guests if guest.availability_provided)
        pending_count = total_guests - responded_count
        
        print(f"Total guests: {total_guests}")
        print(f"Responded: {responded_count}")
        print(f"Pending: {pending_count}")
        
        print(f"\nGuest details:")
        for guest in active_event.guests:
            print(f"  {guest.name}: availability_provided = {guest.availability_provided}")
        
        # Check if we need to update Jude's status
        jude = next((g for g in active_event.guests if g.name == 'Jude'), None)
        if jude and not jude.availability_provided:
            print(f"\n🔧 Jude has availability record but availability_provided is False")
            print(f"Updating Jude's availability_provided to True...")
            jude.availability_provided = True
            jude.save()
            print("✅ Updated Jude's status")

if __name__ == "__main__":
    check_guest_status()
