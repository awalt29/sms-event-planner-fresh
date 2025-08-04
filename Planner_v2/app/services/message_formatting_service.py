from typing import Dict, List
import logging
from app.models.event import Event
from app.models.guest import Guest

logger = logging.getLogger(__name__)

class MessageFormattingService:
    """Handles all message formatting with consistent emoji usage"""
    
    def format_planner_confirmation_menu(self, event: Event) -> str:
        """Generate 3-option confirmation menu"""
        guest_list = "\n".join([f"- {guest.name} ({guest.phone_number})" for guest in event.guests])
        
        response_text = "Got it, planning for:\n"
        if event.notes and "Proposed dates:" in event.notes:
            dates_text = event.notes.split("Proposed dates: ")[1].split("\n")[0]
            response_text += f"- {dates_text}\n"
        
        response_text += f"\nGuest list:\n{guest_list}\n\n"
        response_text += "Would you like to:\n"
        response_text += "1. Request guest availability\n"
        response_text += "2. Change the dates\n"
        response_text += "3. Add more guests\n\n"
        response_text += "Reply with 1, 2, or 3."
        
        return response_text
    
    def format_availability_status(self, event: Event) -> str:
        """Create availability tracking summary"""
        total_guests = len(event.guests)
        provided_count = sum(1 for guest in event.guests if guest.availability_provided)
        pending_count = total_guests - provided_count
        
        status_text = f"📊 Availability Status:\n\n"
        status_text += f"✅ Responded: {provided_count}/{total_guests}\n"
        status_text += f"⏳ Pending: {pending_count}\n\n"
        
        if pending_count > 0:
            pending_guests = [guest for guest in event.guests if not guest.availability_provided]
            status_text += "Still waiting for:\n"
            for guest in pending_guests:
                status_text += f"- {guest.name}\n"
            status_text += "\nSend 'remind' to send follow-up messages."
        else:
            status_text += "🎉 Everyone has responded!\n\n"
            status_text += "Would you like to:\n"
            status_text += "1. Pick a time\n"
            status_text += "2. Add more guests"
        
        return status_text
    
    def format_venue_suggestions(self, venues: List[Dict], activity: str, location: str) -> str:
        """Format venue options with Google Maps links"""
        response_text = f"🎯 Perfect! Looking for {activity} in {location}.\n\n"
        response_text += "Here are some great options:\n\n"
        
        for i, venue in enumerate(venues, 1):
            response_text += f"{i}. {venue.get('name', 'Unknown venue')}\n"
            response_text += f"{venue.get('link', '')}\n"
            if venue.get('description'):
                response_text += f"- {venue['description']}\n\n"
            else:
                response_text += "\n"
        
        response_text += "Select an option (1,2,3) or say:\n"
        response_text += "- 'New list' for more options\n"
        response_text += "- 'Activity' to change the activity\n"
        response_text += "- 'Location' to change the location"
        
        return response_text
    
    def format_guest_invitation(self, event: Event, guest: Guest) -> str:
        """Create final invitation message"""
        # Format date and time
        date_obj = event.start_date
        formatted_date = date_obj.strftime('%A, %B %-d') if date_obj else "TBD"
        
        if event.start_time and event.end_time:
            start_time = event.start_time.strftime('%I:%M%p').lower()
            end_time = event.end_time.strftime('%I:%M%p').lower()
            time_str = f"{start_time}-{end_time}"
        else:
            time_str = "All day"
        
        # Get venue details
        venue_info = "Selected venue"
        venue_link = ""
        if event.selected_venue:
            try:
                import json
                venue_data = json.loads(event.selected_venue)
                venue_info = venue_data.get('name', 'Selected venue')
                venue_link = venue_data.get('link', '')
            except:
                pass
        
        invitation_msg = f"🎉 You're invited!\n\n"
        invitation_msg += f"📅 Date: {formatted_date}\n"
        invitation_msg += f"🕒 Time: {time_str}\n"
        invitation_msg += f"🏢 Venue: {venue_info}\n"
        if venue_link:
            invitation_msg += f"{venue_link}\n"
        invitation_msg += f"\nPlanned by: {event.planner.name or 'Your event planner'}\n\n"
        invitation_msg += "Please reply 'Yes', 'No', or 'Maybe' to confirm your attendance!"
        
        return invitation_msg
    
    def format_time_selection_options(self, overlaps: List[Dict]) -> str:
        """Format time selection with overlaps"""
        if not overlaps:
            return "❌ No overlapping times found. You may need to add more flexibility or different dates."
        
        response_text = "🕒 Best available timeslots:\n\n"
        
        for i, overlap in enumerate(overlaps, 1):
            date_obj = overlap['date']
            formatted_date = date_obj.strftime('%a, %-m/%-d') if date_obj else "TBD"
            
            start_time = overlap.get('start_time', '00:00')
            end_time = overlap.get('end_time', '23:59')
            
            # Convert to readable format
            if start_time == '00:00' and end_time == '23:59':
                time_str = "All day"
            else:
                time_str = f"{start_time}-{end_time}"
            
            guest_count = overlap.get('guest_count', 0)
            total_guests = len(overlap.get('available_guests', []))
            attendance = round((guest_count / max(total_guests, 1)) * 100)
            
            response_text += f"{i}. {formatted_date}: {time_str}\n"
            response_text += f"Attendance: {attendance}%\n"
            response_text += f"Available: {', '.join(overlap.get('available_guests', []))}\n\n"
        
        response_text += "Reply with the number of your preferred option (e.g. 1,2,3)"
        
        return response_text

    def format_final_confirmation(self, event: Event) -> str:
        """Format final confirmation with all event details"""
        # Get date info
        if event.notes and "Proposed dates:" in event.notes:
            dates_text = event.notes.split("Proposed dates: ")[1].split("\n")[0]
        else:
            dates_text = "TBD"
        
        # Get time info
        if event.notes and "Selected time:" in event.notes:
            time_text = event.notes.split("Selected time: ")[1].split("\n")[0]
        else:
            time_text = "TBD"
        
        # Get venue info
        venue_name = "TBD"
        if event.selected_venue:
            venue_name = event.selected_venue.get('name', 'Selected venue')
        
        # Get guest list
        guest_names = [guest.name for guest in event.guests]
        guest_list = ', '.join(guest_names)
        
        confirmation_msg = "🎉 Event Ready to Send!\n\n"
        confirmation_msg += f"📅 Date: {dates_text}\n"
        confirmation_msg += f"🕒 Time: {time_text}\n"
        confirmation_msg += f"📍 Location: {event.location or 'TBD'}\n"
        confirmation_msg += f"🏢 Activity: {event.activity or 'TBD'}\n"
        confirmation_msg += f"🏪 Venue: {venue_name}\n"
        confirmation_msg += f"👥 Attendees: {guest_list}\n\n"
        confirmation_msg += "Would you like to:\n"
        confirmation_msg += "1. Send invitations to guests\n"
        confirmation_msg += "Or reply 'restart' to start over with a new event"
        
        return confirmation_msg
