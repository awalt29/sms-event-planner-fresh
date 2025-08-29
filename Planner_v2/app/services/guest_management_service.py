from typing import Dict, List, Optional
import logging
from app.models.event import Event
from app.models.guest import Guest
from app.models.guest_state import GuestState
from app.models.contact import Contact

logger = logging.getLogger(__name__)

class GuestManagementService:
    """Manages guest addition, availability, and RSVP tracking"""
    
    def __init__(self):
        from app.services.sms_service import SMSService
        from app.services.message_formatting_service import MessageFormattingService
        self.sms_service = SMSService()
        self.message_service = MessageFormattingService()
    
    def add_guest_to_event(self, event_id: int, name: str, phone: str = None) -> Guest:
        """Add a single guest to an event"""
        try:
            # Normalize phone number
            normalized_phone = self._normalize_phone(phone) if phone else 'N/A'
            
            # Check for existing guest
            existing = Guest.query.filter_by(
                event_id=event_id,
                phone_number=normalized_phone
            ).first()
            
            if existing:
                return existing
            
            # Create new guest
            guest = Guest(
                event_id=event_id,
                name=name,
                phone_number=normalized_phone,
                rsvp_status='pending',
                availability_provided=False,
                preferences_provided=False
            )
            guest.save()
            
            # Save as contact for future use if phone provided
            if phone and phone != 'N/A':
                from app.models.event import Event
                event = Event.query.get(event_id)
                if event:
                    self._save_as_contact(event_id, {'name': name, 'phone_number': normalized_phone})
            
            return guest
            
        except Exception as e:
            logger.error(f"Error adding guest: {e}")
            return None

    def add_guests_from_text(self, event_id: int, text: str) -> Dict:
        """Legacy method - parse guest information from text and add to event"""
        try:
            # Parse guest info using regex patterns only (AI parsing moved to handlers)
            parsed_guests = self._parse_guest_text(text)
            
            if not parsed_guests:
                return {'success': False, 'error': 'Could not parse guest information'}
            
            added_guests = []
            for guest_data in parsed_guests:
                guest = self.add_guest_to_event(
                    event_id, 
                    guest_data['name'], 
                    guest_data.get('phone_number')
                )
                if guest:
                    added_guests.append(guest)
            
            return {'success': True, 'guests': added_guests}
            
        except Exception as e:
            logger.error(f"Error adding guests: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_availability_request(self, guest: Guest) -> bool:
        """Send availability request to guest"""
        try:
            event = guest.event
            planner = event.planner
            
            # Format availability request message
            message = self._format_availability_request(guest, event, planner)
            
            # Send SMS
            success = self.sms_service.send_sms(guest.phone_number, message)
            
            if success:
                # Normalize phone number for guest state (consistent with router normalization)
                normalized_phone = self._normalize_phone(guest.phone_number)
                
                # Prepare context data with event dates
                context_data = self._prepare_availability_context(event)
                
                # Create or update guest state for tracking response
                existing_state = GuestState.query.filter_by(phone_number=normalized_phone).first()
                if existing_state:
                    # Update existing state
                    existing_state.event_id = event.id
                    existing_state.current_state = 'awaiting_availability'
                    existing_state.set_state_data(context_data)
                    existing_state.save()
                else:
                    # Create new state
                    guest_state = GuestState(
                        phone_number=normalized_phone,
                        event_id=event.id,
                        current_state='awaiting_availability'
                    )
                    guest_state.set_state_data(context_data)
                    guest_state.save()
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending availability request: {e}")
            return False
    
    def _parse_guest_text(self, text: str) -> List[Dict]:
        """Parse guest information from text input using regex patterns only"""
        import re
        
        # Pattern for name and phone number
        pattern = r'([^,]+),\s*([0-9\-\(\)\s]+)'
        matches = re.findall(pattern, text)
        
        guests = []
        for name, phone in matches:
            normalized_phone = self._normalize_phone(phone.strip())
            if normalized_phone:
                guests.append({
                    'name': name.strip(),
                    'phone_number': normalized_phone
                })
        
        # If no comma-separated format, try space-separated (name followed by phone)
        if not guests:
            space_pattern = r'([A-Za-z\s]+)\s+(\d{10,})'
            space_match = re.search(space_pattern, text)
            if space_match:
                name = space_match.group(1).strip()
                phone = space_match.group(2).strip()
                normalized_phone = self._normalize_phone(phone)
                if normalized_phone:
                    guests.append({
                        'name': name,
                        'phone_number': normalized_phone
                    })
        
        return guests
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to standard format"""
        # Remove all non-digits
        digits = ''.join(filter(str.isdigit, phone))
        
        # Handle different formats
        if len(digits) == 10:
            return digits
        elif len(digits) == 11 and digits.startswith('1'):
            return digits[1:]
        
        return None

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

    def _format_availability_request(self, guest: Guest, event: Event, planner) -> str:
        """Format availability request message for guest"""
        # Format dates as individual list items
        date_list = self._format_dates_for_guest_request(event)
        
        # Format guest list (excluding the current recipient)
        guest_list = self._format_guest_list_for_request(event, guest)
        
        message = f"Hi {self._extract_first_name(guest.name)}! {self._extract_first_name(planner.name) if planner.name else 'Your planner'} wants to hang out on one of these days:\n\n"
        message += f"{date_list}\n\n"
        
        # Add guest list if there are other guests
        if guest_list:
            message += f"{guest_list}\n\n"
        
        message += "Reply with your availability and we'll find common times!🗓️ \n\nYou can say things like:\n\n"
        message += "- 'Friday 2-6pm, Saturday after 4pm'\n"
        message += "- 'Friday all day, Saturday evening'\n"
        message += "- 'Friday after 3pm'\n"
        message += "- 'Busy' (if you're not available any of these days)"
        
        return message
    
    def _format_guest_list_for_request(self, event: Event, current_guest: Guest) -> str:
        """Format guest list for availability request, excluding the current recipient"""
        # Get all other guests (excluding the current recipient)
        other_guests = [g for g in event.guests if g.id != current_guest.id]
        
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
    
    def _format_dates_for_guest_request(self, event: Event) -> str:
        """Format dates as individual list items for guest requests"""
        try:
            # Extract dates from JSON storage if available
            if event.notes and "Dates JSON:" in event.notes:
                import json
                from datetime import datetime
                dates_json_part = event.notes.split("Dates JSON: ")[1].split("\n")[0]
                dates = json.loads(dates_json_part)
                
                # Format each date as a list item
                formatted_dates = []
                for date_str in dates:
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        formatted_date = date_obj.strftime('%A, %B %-d')
                        formatted_dates.append(f"- {formatted_date}")
                    except ValueError:
                        formatted_dates.append(f"- {date_str}")
                
                return '\n'.join(formatted_dates)
            
            # Fallback to old format
            elif event.notes and "Proposed dates:" in event.notes:
                dates_text = event.notes.split("Proposed dates: ")[1].split("\n")[0]
                return f"- {dates_text}"
            
            return "- the proposed dates"
            
        except Exception as e:
            logger.error(f"Date formatting error for guest request: {e}")
            return "- the proposed dates"
    
    def _save_as_contact(self, event_id: int, guest_data: Dict):
        """Save guest as contact for future use"""
        try:
            event = Event.query.get(event_id)
            if event:
                # Check if contact already exists
                existing_contact = Contact.query.filter_by(
                    planner_id=event.planner_id,
                    phone_number=guest_data['phone_number']
                ).first()
                
                if not existing_contact:
                    contact = Contact(
                        planner_id=event.planner_id,
                        name=guest_data['name'],
                        phone_number=guest_data['phone_number']
                    )
                    contact.save()
        except Exception as e:
            logger.error(f"Error saving contact: {e}")

    def send_event_invitation(self, guest: Guest) -> bool:
        """Send final event invitation to guest"""
        try:
            event = guest.event
            
            # Format invitation message
            message = self.message_service.format_guest_invitation(event, guest)
            
            # Send SMS
            success = self.sms_service.send_sms(guest.phone_number, message)
            
            if success:
                # Normalize phone number for guest state (consistent with router normalization)
                normalized_phone = self._normalize_phone(guest.phone_number)
                
                # Create or update guest state for RSVP tracking
                existing_state = GuestState.query.filter_by(phone_number=normalized_phone).first()
                if existing_state:
                    # Update existing state
                    existing_state.event_id = event.id
                    existing_state.current_state = 'awaiting_rsvp'
                    existing_state.save()
                else:
                    # Create new state
                    guest_state = GuestState(
                        phone_number=normalized_phone,
                        event_id=event.id,
                        current_state='awaiting_rsvp'
                    )
                    guest_state.save()
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending invitation: {e}")
            return False
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to standard format (consistent with SMS router)"""
        # Remove all non-digits
        digits = ''.join(filter(str.isdigit, phone))
        
        # Handle different formats
        if len(digits) == 10:
            return digits
        elif len(digits) == 11 and digits.startswith('1'):
            return digits[1:]
        
        return digits  # Return as-is if can't normalize
    
    def _prepare_availability_context(self, event: Event) -> dict:
        """Prepare context data for availability parsing"""
        try:
            context = {}
            
            # Extract event dates from notes if available
            if event.notes and "Dates JSON:" in event.notes:
                import json
                dates_json_part = event.notes.split("Dates JSON: ")[1].split("\n")[0]
                dates = json.loads(dates_json_part)
                context['event_dates'] = dates
            
            return context
            
        except Exception as e:
            logger.error(f"Error preparing availability context: {e}")
            return {}
