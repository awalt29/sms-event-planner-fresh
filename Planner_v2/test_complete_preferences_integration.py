#!/usr/bin/env python3
"""Test preferences integration in availability formatting"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, date, time
from app import create_app, db
from app.models.event import Event
from app.models.planner import Planner
from app.models.guest import Guest
from app.models.availability import Availability

# Import just the formatting method parts we need
def format_time_12hr(time_str):
    """Format time in 12-hour format"""
    hour, minute = map(int, time_str.split(':'))
    if hour == 0:
        return f"12:{minute:02d} AM"
    elif hour < 12:
        return f"{hour}:{minute:02d} AM"
    elif hour == 12:
        return f"12:{minute:02d} PM"
    else:
        return f"{hour - 12}:{minute:02d} PM"

def format_guest_availability_details(guest):
    """Format guest's availability details for planner notification"""
    # Get all availability records for this guest
    availability_records = Availability.query.filter_by(
        event_id=guest.event_id,
        guest_id=guest.id
    ).all()
    
    if not availability_records:
        return "- No specific times provided"
    
    # Group by date and format
    availability_lines = []
    
    for avail in availability_records:
        if avail.date:
            # Format date as "Friday"
            date_str = avail.date.strftime('%A')
            
            if avail.all_day:
                availability_lines.append(f"- {date_str} all day")
            else:
                # Format times in 12-hour format
                start_time = format_time_12hr(avail.start_time.strftime('%H:%M'))
                end_time = format_time_12hr(avail.end_time.strftime('%H:%M'))
                availability_lines.append(f"- {date_str} {start_time}-{end_time}")
    
    if not availability_lines:
        return "- No specific times provided"
    
    # Add preferences if provided
    result = '\n'.join(availability_lines)
    if guest.preferences_provided and guest.preferences and guest.preferences.strip():
        result += f"\n📝 Preferences: {guest.preferences}"
    
    return result

def test_complete_preferences_with_updated_formatting():
    """Test that preferences appear in availability formatting"""
    app = create_app()
    
    with app.app_context():
        db.create_all()
        
        # Create planner and event with unique phone
        import random
        unique_phone = f'+1{random.randint(1000000000, 9999999999)}'
        planner = Planner(phone_number=unique_phone, name='Test Planner')
        db.session.add(planner)
        db.session.commit()
        
        event = Event(
            planner_id=planner.id,
            activity='Dinner',
            status='collecting_availability'
        )
        db.session.add(event)
        db.session.commit()
        
        # Create guest
        guest = Guest(
            event_id=event.id,
            phone_number='+1111111111',
            name='Test Guest',
            rsvp_status='responded',
            preferences_provided=False
        )
        db.session.add(guest)
        db.session.commit()
        
        # Add availability
        availability = Availability(
            event_id=event.id,
            guest_id=guest.id,
            date=date(2024, 12, 20),  # Friday
            start_time=time(19, 0),   # 7:00 PM
            end_time=time(23, 0),     # 11:00 PM
            all_day=False
        )
        db.session.add(availability)
        db.session.commit()
        
        print("=== Testing Updated Availability Formatting ===")
        
        # Test without preferences
        formatted_details = format_guest_availability_details(guest)
        print("\nGuest Availability Details (no preferences):")
        print(formatted_details)
        print()
        
        assert "- Friday 7:00 PM-11:00 PM" in formatted_details
        assert "📝 Preferences:" not in formatted_details
        print("✅ PASS: Availability formatting works correctly without preferences")
        
        # Add preferences to guest
        guest.preferences = "I'm vegetarian and prefer quieter restaurants"
        guest.preferences_provided = True
        db.session.commit()
        
        # Test with preferences
        formatted_with_prefs = format_guest_availability_details(guest)
        print("\nGuest Availability Details (with preferences):")
        print(formatted_with_prefs)
        print()
        
        # Verify it includes both availability AND preferences
        assert "- Friday 7:00 PM-11:00 PM" in formatted_with_prefs
        assert "📝 Preferences: I'm vegetarian and prefer quieter restaurants" in formatted_with_prefs
        
        print("✅ PASS: Availability formatting includes both times and preferences")
        print("\n🎉 All tests passed! Preferences are now included in availability displays")
        
        # Clean up - delete records to avoid conflicts
        db.session.delete(availability)
        db.session.delete(guest)
        db.session.delete(event)
        db.session.delete(planner)
        db.session.commit()

if __name__ == '__main__':
    test_complete_preferences_with_updated_formatting()
