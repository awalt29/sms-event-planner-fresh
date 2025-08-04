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
        self.sms_service = SMSService()
    
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
                availability_provided=False
            )
            guest.save()
            
            # Save as contact for future use if phone provided
            if phone and phone != 'N/A':
                from app.models.event import Event
                event = Event.query.get(event_id)
                if event:
                    self._save_as_contact(event.planner_id, {'name': name, 'phone_number': normalized_phone})
            
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
                # Create guest state for tracking response
                guest_state = GuestState(
                    phone_number=guest.phone_number,
                    event_id=event.id,
                    current_state='awaiting_availability'
                )
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
        
        if guests:
            logger.info(f"Regex parsed {len(guests)} guests successfully")
        else:
            logger.warning(f"Could not parse guest information from: '{text}'")
        
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

    def _format_availability_request(self, guest: Guest, event: Event, planner) -> str:
        """Format availability request message for guest"""
        # Parse dates from event notes
        dates_text = "the proposed dates"
        if event.notes and "Proposed dates:" in event.notes:
            dates_text = event.notes.split("Proposed dates: ")[1].split("\n")[0]
        
        message = f"Hi {guest.name}! {planner.name} wants to hang out on one of these days:\n\n"
        message += f"- {dates_text}\n\n"
        message += "Reply with your availability. You can say things like:\n\n"
        message += "- 'Friday 2-6pm, Saturday after 4pm'\n"
        message += "- 'Friday all day, Saturday evening'\n"
        message += "- 'Friday after 3pm'"
        
        return message
    
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
                # Create guest state for RSVP tracking
                guest_state = GuestState(
                    phone_number=guest.phone_number,
                    event_id=event.id,
                    current_state='awaiting_rsvp'
                )
                guest_state.save()
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending invitation: {e}")
            return False
