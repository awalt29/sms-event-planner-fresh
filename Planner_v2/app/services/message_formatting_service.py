from typing import Dict, List
import logging
from app.models.event import Event
from app.models.guest import Guest

logger = logging.getLogger(__name__)

class MessageFormattingService:
    """Handles all message formatting with consistent emoji usage"""
    
    def _extract_first_name(self, full_name: str) -> str:
        """Extract first name from full name, handling titles"""
        if not full_name:
            return "Friend"
        
        # Split by spaces and clean up
        name_parts = full_name.strip().split()
        if not name_parts:
            return full_name.strip() or "Friend"
        
        # Common titles to skip
        titles = {'dr.', 'dr', 'mr.', 'mr', 'mrs.', 'mrs', 'ms.', 'ms', 'prof.', 'prof'}
        
        # Find the first non-title word
        for part in name_parts:
            if part.lower().rstrip('.') not in titles:
                return part
        
        # If all parts are titles, just use the first one
        return name_parts[0]
    
    def _format_time_12hr(self, time_str: str) -> str:
        """Convert 24-hour format to 12-hour format"""
        try:
            from datetime import datetime
            # Parse the time string (HH:MM format)
            time_obj = datetime.strptime(time_str, '%H:%M')
            # Format to 12-hour with am/pm
            formatted = time_obj.strftime('%I:%M%p').lower()
            # Remove leading zero from hour and :00 for cleaner look
            if formatted.startswith('0'):
                formatted = formatted[1:]  # Remove leading zero
            # Remove :00 for on-the-hour times (12:00pm becomes 12pm)
            if ':00' in formatted:
                formatted = formatted.replace(':00', '')
            return formatted
        except ValueError:
            # If parsing fails, return original
            return time_str
    
    def _format_phone_display(self, phone_number: str) -> str:
        """Format phone number for display"""
        if not phone_number:
            return phone_number
        
        # Remove + and any non-digits
        digits = ''.join(filter(str.isdigit, phone_number))
        
        # Remove country code if present: +12167046177 -> 2167046177
        if len(digits) == 11 and digits.startswith('1'):
            digits = digits[1:]  # Remove country code
        
        # Return just the 10 digits for consistency with the rest of the app
        if len(digits) == 10:
            return digits
        
        # If not a standard 10-digit number, return as-is
        return phone_number
    
    def format_planner_confirmation_menu(self, event: Event) -> str:
        """Generate 3-option confirmation menu"""
        guest_list = "\n".join([f"- {guest.name} ({self._format_phone_display(guest.phone_number)})" for guest in event.guests])
        
        response_text = "Got it, planning for:\n"
        
        # Format dates as individual list items
        if event.notes and "Dates JSON:" in event.notes:
            # Extract dates from JSON storage
            try:
                import json
                from datetime import datetime
                dates_json_part = event.notes.split("Dates JSON: ")[1].split("\n")[0]
                dates = json.loads(dates_json_part)
                
                # Format each date as a list item
                for date_str in dates:
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        formatted_date = date_obj.strftime('%A, %B %-d')
                        response_text += f"- {formatted_date}\n"
                    except ValueError:
                        response_text += f"- {date_str}\n"
            except (json.JSONDecodeError, IndexError):
                # Fallback to old format
                if "Proposed dates:" in event.notes:
                    dates_text = event.notes.split("Proposed dates: ")[1].split("\n")[0]
                    response_text += f"- {dates_text}\n"
        elif event.notes and "Proposed dates:" in event.notes:
            # Fallback for old format
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
            status_text += "\nSend 'remind' to send follow-up messages.\n"
        else:
            status_text += "🎉 Everyone has responded!\n\n"
            status_text += "Would you like to:\n"
            status_text += "1. Pick a time\n"
            status_text += "2. Add more guests\n"
        
        # Show overlap option if we have at least one response
        if provided_count > 0:
            if pending_count > 0:
                status_text += f"\nPress 1 to view current overlaps"
            # If everyone responded, the overlap option is already shown as "1. Pick a time"
        
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
        
        response_text += "Select an option (1,2,3) or select:\n"
        response_text += "4. Generate a new list\n"
        response_text += "5. Select a new activity\n\n"
        
        return response_text
    
    def format_guest_invitation(self, event: Event, guest: Guest) -> str:
        """Create final invitation message"""
        # Format date and time - use selected_ fields from time selection
        date_obj = event.selected_date or event.start_date
        formatted_date = date_obj.strftime('%A, %B %-d') if date_obj else "TBD"
        
        # Use selected time fields if available, fallback to original fields
        start_time = event.selected_start_time or event.start_time
        end_time = event.selected_end_time or event.end_time
        
        if start_time:
            start_time_str = self._format_time_12hr(start_time.strftime('%H:%M'))
            
            # Show just start time if user specifically set it, otherwise show range
            if event.notes and "USER_SET_START_TIME=True" in event.notes:
                time_str = start_time_str  # Just show "4pm"
            elif end_time:
                # System-selected or original time, show full range
                end_time_str = self._format_time_12hr(end_time.strftime('%H:%M'))
                time_str = f"{start_time_str}-{end_time_str}"
            else:
                time_str = start_time_str
        else:
            time_str = "All day"
        
        # Get venue details
        venue_info = "Selected venue"
        venue_link = ""
        if event.selected_venue:
            logger.info(f"Raw venue data: {event.selected_venue} (type: {type(event.selected_venue)})")
            try:
                # Handle both dict and JSON string formats
                if isinstance(event.selected_venue, dict):
                    venue_data = event.selected_venue
                else:
                    import json
                    venue_data = json.loads(event.selected_venue)
                
                venue_info = venue_data.get('name', 'Selected venue')
                venue_link = venue_data.get('link', '')
                logger.info(f"Parsed venue: {venue_info}, link: {venue_link}")
            except Exception as e:
                logger.error(f"Error parsing venue data: {e}")
                # Fallback to check if it's a simple string
                if isinstance(event.selected_venue, str) and not event.selected_venue.startswith('{'):
                    venue_info = event.selected_venue
        elif event.activity:
            # Check activity field for venue name
            venue_info = event.activity
        else:
            logger.warning("No selected_venue or activity data found")
        
        invitation_msg = f"🎉 You're invited!\n\n"
        invitation_msg += f"📅 Date: {formatted_date}\n"
        invitation_msg += f"🕒 Time: {time_str}\n"
        invitation_msg += f"🏢 Venue: {venue_info}\n"
        if venue_link:
            invitation_msg += f"{venue_link}\n"
        
        # Add guest list (excluding the current recipient)
        guest_list = self._format_guest_list_for_invitation(event, guest)
        if guest_list:
            invitation_msg += f"\n{guest_list}\n"
        
        invitation_msg += f"\nPlanned by: {self._extract_first_name(event.planner.name) if event.planner.name else 'Your planner'}\n\n"
        invitation_msg += "Please reply 'Yes', 'No', or 'Maybe' to confirm your attendance!"
        
        return invitation_msg
    
    def format_time_selection_options(self, overlaps: List[Dict], event: Event = None) -> str:
        """Format time selection with overlaps"""
        if not overlaps:
            if event:
                return self._format_no_overlap_message(event)
            else:
                return "❌ No overlapping times found. You may need to add more flexibility or different dates."
        
        response_text = "🕒 Best available timeslots:\n\n"
        
        for i, overlap in enumerate(overlaps, 1):
            date_obj = overlap['date']
            formatted_date = date_obj.strftime('%a, %-m/%-d') if date_obj else "TBD"
            
            start_time = overlap.get('start_time', '00:00')
            end_time = overlap.get('end_time', '23:59')
            
            # Convert to readable format
            if start_time == '08:00' and end_time == '23:59':
                time_str = "All day"
            else:
                # Convert to 12-hour format
                start_12hr = self._format_time_12hr(start_time)
                end_12hr = self._format_time_12hr(end_time)
                time_str = f"{start_12hr}-{end_12hr}"
            
            guest_count = overlap.get('guest_count', 0)
            # Get total guests in the event for proper attendance calculation
            event_total_guests = len(event.guests) if event else guest_count
            attendance = round((guest_count / max(event_total_guests, 1)) * 100)
            
            response_text += f"{i}. {formatted_date}: {time_str}\n"
            response_text += f"Attendance: {attendance}%\n"
            response_text += f"Available: {', '.join(overlap.get('available_guests', []))}\n\n"
        
        response_text += "Reply with the number of your preferred option (e.g. 1,2,3)"
        
        return response_text

    def _format_no_overlap_message(self, event: Event) -> str:
        """Format detailed message when no overlapping times are found"""
        from app.models.availability import Availability
        from app import db
        from datetime import datetime
        
        message = "❌ No overlapping times found.\n\n"
        message += "Guest availability:\n\n"
        
        # Get all unique dates from availability records for this event
        availability_dates = db.session.query(Availability.date).filter_by(event_id=event.id).distinct().all()
        event_dates = [date_tuple[0] for date_tuple in availability_dates if date_tuple[0]]
        event_dates.sort()
        
        for event_date in event_dates:
            # Format date with day of week and full date
            formatted_date = event_date.strftime('%A, %B %-d')
            # Only show year if different from current year
            current_year = datetime.now().year
            if event_date.year != current_year:
                formatted_date += f", {event_date.year}"
            
            message += f"📅 {formatted_date}\n\n"
            
            # Get availability for each guest on this date
            for guest in event.guests:
                message += f"👤 {guest.name}\n"
                
                # Find availability for this guest on this date
                availability = Availability.query.filter_by(
                    event_id=event.id,
                    guest_id=guest.id,
                    date=event_date
                ).first()
                
                if availability:
                    start_time = self._format_time_12hr(availability.start_time.strftime('%H:%M'))
                    end_time = self._format_time_12hr(availability.end_time.strftime('%H:%M'))
                    message += f"🕒 {start_time} - {end_time}\n\n"
                else:
                    message += "- Not available\n\n"
        
        message += "Say 'restart' to try with new guests or dates"
        return message

    def format_final_confirmation(self, event: Event) -> str:
        """Format final confirmation with all event details"""
        # Get date and time info from selected data
        if event.selected_date:
            date_text = event.selected_date.strftime('Tuesday, August %-d')
            if event.selected_start_time:
                start_time = self._format_time_12hr(event.selected_start_time.strftime('%H:%M'))
                
                # Show just start time if user specifically set it, otherwise show range
                if event.notes and "USER_SET_START_TIME=True" in event.notes:
                    time_text = start_time  # Just show "4pm"
                elif event.selected_end_time:
                    # System-selected time overlap, show full range
                    end_time = self._format_time_12hr(event.selected_end_time.strftime('%H:%M'))
                    time_text = f"{start_time}-{end_time}"
                else:
                    time_text = start_time
            else:
                time_text = "All day"
        else:
            # Fallback to notes parsing
            if event.notes and "Proposed dates:" in event.notes:
                date_text = event.notes.split("Proposed dates: ")[1].split("\n")[0]
            else:
                date_text = "TBD"
            
            if event.notes and "Selected time:" in event.notes:
                time_text = event.notes.split("Selected time: ")[1].split("\n")[0]
            else:
                time_text = "TBD"
        
        # Get venue info
        venue_name = "TBD"
        if event.selected_venue:
            venue_name = event.selected_venue.get('name', 'Selected venue')
        elif event.activity:
            venue_name = event.activity
        
        # Get guest list
        guest_names = [guest.name for guest in event.guests]
        guest_list = ', '.join(guest_names)
        
        confirmation_msg = "🎉 Event Ready to Send!\n\n"
        confirmation_msg += f"📅 Date: {date_text}\n"
        confirmation_msg += f"🕒 Time: {time_text}\n"
        confirmation_msg += f"🏪 Venue: {venue_name}\n"
        confirmation_msg += f"👥 Attendees: {guest_list}\n\n"
        confirmation_msg += "Would you like to:\n"
        confirmation_msg += "1. Set a start time\n"
        confirmation_msg += "2. Send invitations to guests\n"
        confirmation_msg += "3. Change the activity\n\n"
        confirmation_msg += "Or reply 'restart' to start over" 
        
        return confirmation_msg
    
    def _format_guest_list_for_invitation(self, event: Event, current_guest: Guest) -> str:
        """Format guest list for final invitation, using selected available guests if time was selected"""
        try:
            # First try to get the guests who are available for the selected time
            if event.notes and "Selected available guests:" in event.notes:
                import json
                # Extract the JSON list from notes
                guests_json_part = event.notes.split("Selected available guests: ")[1].split("\n")[0]
                available_guest_names = json.loads(guests_json_part)
                
                # Filter out the current recipient
                other_guests = [name for name in available_guest_names if name != current_guest.name]
                
                if not other_guests:
                    return ""  # No other guests available for selected time
                
                # Use the same formatting logic as availability requests
                if len(other_guests) == 1:
                    return f"👥 With: {other_guests[0]}"
                elif len(other_guests) == 2:
                    return f"👥 With: {other_guests[0]} and {other_guests[1]}"
                else:
                    # For 3+ guests: "With: Alex, Mike, and Lisa"
                    return f"👥 With: {', '.join(other_guests[:-1])}, and {other_guests[-1]}"
            
            # Fallback: use all event guests (excluding current recipient)  
            other_guests = [g for g in event.guests if g.id != current_guest.id and g.name]
            
            if not other_guests:
                return ""  # No other guests to show
            
            # Extract first names only for cleaner display
            guest_names = [self._extract_first_name(g.name) for g in other_guests]
            
            # Format the list with proper grammar
            if len(guest_names) == 1:
                return f"👥 With: {guest_names[0]}"
            elif len(guest_names) == 2:
                return f"👥 With: {guest_names[0]} and {guest_names[1]}"
            else:
                # For 3+ guests: "With: Alex, Mike, and Lisa"
                return f"👥 With: {', '.join(guest_names[:-1])}, and {guest_names[-1]}"
                
        except Exception as e:
            logger.error(f"Error formatting guest list for invitation: {e}")
            return ""  # Don't show guest list if there's an error
    
    def format_guest_availability_details(self, guest) -> str:
        """Format a guest's availability details for planner notifications"""
        try:
            from app.models.availability import Availability
            from datetime import datetime
            
            # Get all availability records for this guest
            availability_records = Availability.query.filter_by(guest_id=guest.id).all()
            
            if not availability_records:
                return "- No specific availability provided"
            
            # Group availability by date
            availability_by_date = {}
            for record in availability_records:
                if record.date:
                    date_str = record.date.strftime('%A')  # e.g., "Friday"
                    if date_str not in availability_by_date:
                        availability_by_date[date_str] = []
                    availability_by_date[date_str].append(record)
            
            if not availability_by_date:
                return "- No specific availability provided"
            
            # Format each day's availability
            formatted_lines = []
            for date_str, records in availability_by_date.items():
                # Check if any record is all day
                all_day_records = [r for r in records if r.all_day]
                if all_day_records:
                    formatted_lines.append(f"- {date_str}: All day")
                else:
                    # Format time ranges
                    time_ranges = []
                    for record in records:
                        if record.start_time and record.end_time:
                            start_str = self._format_time_12hr(record.start_time.strftime('%H:%M'))
                            end_str = self._format_time_12hr(record.end_time.strftime('%H:%M'))
                            time_ranges.append(f"{start_str}-{end_str}")
                        elif record.start_time:
                            start_str = self._format_time_12hr(record.start_time.strftime('%H:%M'))
                            time_ranges.append(f"after {start_str}")
                        elif record.end_time:
                            end_str = self._format_time_12hr(record.end_time.strftime('%H:%M'))
                            time_ranges.append(f"until {end_str}")
                    
                    if time_ranges:
                        formatted_lines.append(f"- {date_str}: {', '.join(time_ranges)}")
                    else:
                        formatted_lines.append(f"- {date_str}: Available")
            
            return '\n'.join(formatted_lines)
            
        except Exception as e:
            logger.error(f"Error formatting guest availability details: {e}")
            return "- Availability details unavailable"
