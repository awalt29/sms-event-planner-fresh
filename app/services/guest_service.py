from typing import Dict, Any, List
from app.models import db, Guest, Contact, Event, GuestState
from app.utils.phone import normalize_phone, extract_phone_numbers_from_text, validate_phone_number
from app.utils.sms import send_sms
import re
import logging

logger = logging.getLogger(__name__)


class GuestService:
    """Service class for guest-related business logic."""
    
    def add_guests_from_text(self, event_id: int, text: str) -> Dict[str, Any]:
        """
        Add guests to an event from natural language text.
        
        Args:
            event_id: ID of the event
            text: Text containing guest information (names and phone numbers)
            
        Returns:
            dict: Result with success status and details
        """
        try:
            event = Event.query.get(event_id)
            if not event:
                return {
                    'success': False,
                    'error': 'Event not found'
                }
            
            # Parse guest information from text
            guests_info = self._parse_guests_from_text(text)
            
            if not guests_info:
                return {
                    'success': False,
                    'error': 'Could not find any guest information. Please include names and phone numbers.'
                }
            
            added_guests = []
            errors = []
            
            for guest_info in guests_info:
                result = self._add_single_guest(event, guest_info)
                if result['success']:
                    added_guests.append(result['guest'])
                else:
                    errors.append(result['error'])
            
            if added_guests:
                # Don't automatically send availability requests - wait for planner confirmation
                return {
                    'success': True,
                    'added_count': len(added_guests),
                    'guests': added_guests,
                    'errors': errors
                }
            else:
                return {
                    'success': False,
                    'error': f"Failed to add guests: {'; '.join(errors)}"
                }
            
        except Exception as e:
            logger.error(f"Error adding guests from text: {e}")
            return {
                'success': False,
                'error': 'Failed to add guests. Please try again.'
            }
    
    def _parse_guests_from_text(self, text: str) -> List[Dict[str, str]]:
        """
        Parse guest information (names and phone numbers) from text.
        
        Args:
            text: Text containing guest information
            
        Returns:
            list: List of guest information dictionaries
        """
        guests = []
        
        # Pattern to match "Name (phone)" or "Name phone"
        patterns = [
            r'([A-Za-z\s]+)\s*\(([0-9\-\(\)\s\+]+)\)',  # Name (phone)
            r'([A-Za-z\s]+)\s+([0-9\-\(\)\s\+]{10,})',   # Name phone
            r'([A-Za-z\s]+):\s*([0-9\-\(\)\s\+]+)',      # Name: phone
        ]
        
        found_guests = set()  # To avoid duplicates
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1).strip()
                phone = match.group(2).strip()
                
                # Validate phone number
                normalized_phone = normalize_phone(phone)
                if len(normalized_phone) >= 10:  # Minimum valid phone length
                    guest_key = (name.lower(), normalized_phone)
                    if guest_key not in found_guests:
                        guests.append({
                            'name': name,
                            'phone': normalized_phone
                        })
                        found_guests.add(guest_key)
        
        # If no structured format found, try to extract phone numbers and match with names
        if not guests:
            phone_numbers = extract_phone_numbers_from_text(text)
            
            # Simple heuristic: try to match nearby words as names
            words = text.split()
            for phone in phone_numbers:
                # Look for names near the phone number in the text
                phone_pos = text.find(phone)
                if phone_pos != -1:
                    # Look for words before the phone number that could be names
                    before_text = text[:phone_pos].strip()
                    name_words = before_text.split()[-2:]  # Take last 2 words as potential name
                    
                    if name_words and all(word.isalpha() or word in ['and', '&'] for word in name_words):
                        name = ' '.join(name_words).strip()
                        if name and name.lower() not in ['add', 'invite', 'guest', 'contact']:
                            guests.append({
                                'name': name,
                                'phone': normalize_phone(phone)
                            })
        
        return guests
    
    def _add_single_guest(self, event: Event, guest_info: Dict[str, str]) -> Dict[str, Any]:
        """
        Add a single guest to an event.
        
        Args:
            event: Event object
            guest_info: Dictionary with guest name and phone
            
        Returns:
            dict: Result with success status and guest or error
        """
        try:
            name = guest_info['name']
            phone = guest_info['phone']
            
            # Check if guest already exists for this event
            existing_guest = Guest.query.filter_by(
                event_id=event.id,
                phone_number=phone
            ).first()
            
            if existing_guest:
                return {
                    'success': False,
                    'error': f'{name} is already invited to this event'
                }
            
            # Check if contact exists for this planner
            contact = Contact.query.filter_by(
                planner_id=event.planner_id,
                phone_number=phone
            ).first()
            
            # Create or update contact
            if not contact:
                contact = Contact(
                    planner_id=event.planner_id,
                    name=name,
                    phone_number=phone
                )
                contact.save()
            else:
                # Update name if different
                if contact.name != name:
                    contact.name = name
                    contact.save()
            
            # Create guest
            guest = Guest(
                event_id=event.id,
                contact_id=contact.id,
                name=name,
                phone_number=phone,
                rsvp_status='pending',
                availability_provided=False
            )
            guest.save()
            
            logger.info(f"Added guest {name} ({phone}) to event {event.id}")
            
            return {
                'success': True,
                'guest': guest
            }
            
        except Exception as e:
            logger.error(f"Error adding single guest: {e}")
            return {
                'success': False,
                'error': f'Failed to add {guest_info.get("name", "guest")}'
            }
    
    def send_availability_request(self, guest: Guest) -> bool:
        """
        Send availability request to a guest.
        
        Args:
            guest: Guest object
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            event = guest.event
            planner = event.planner
            
            # Create or update guest state for conversation tracking
            guest_state = GuestState.query.filter_by(phone_number=guest.phone_number).first()
            if not guest_state:
                guest_state = GuestState(
                    phone_number=guest.phone_number,
                    current_state='awaiting_availability',
                    event_id=event.id
                )
                guest_state.save()
            else:
                # Update existing guest state
                guest_state.current_state = 'awaiting_availability'
                guest_state.event_id = event.id
                guest_state.save()
            
            # Get event dates from notes and format them as a list
            dates_info = event.notes if event.notes and "Proposed dates:" in event.notes else ""
            dates_text = dates_info.replace("Proposed dates: ", "") if dates_info else ""
            
            # Try to parse and format dates as a list
            formatted_dates = ""
            if dates_text:
                try:
                    # Import AI parsing function to reparse the dates
                    from app.utils.ai import parse_dates_from_text
                    parsed_dates = parse_dates_from_text(dates_text)
                    
                    if parsed_dates['success'] and 'dates' in parsed_dates and parsed_dates['dates']:
                        for date_obj in parsed_dates['dates']:
                            if isinstance(date_obj, str):
                                # Try to parse the date string
                                try:
                                    from datetime import datetime
                                    date_parsed = datetime.strptime(date_obj, '%Y-%m-%d')
                                    formatted_date = date_parsed.strftime('%A, %B %-d')
                                    formatted_dates += f"- {formatted_date}\n"
                                except:
                                    formatted_dates += f"- {date_obj}\n"
                            else:
                                # Assume it's already a date object
                                try:
                                    formatted_date = date_obj.strftime('%A, %B %-d')
                                    formatted_dates += f"- {formatted_date}\n"
                                except:
                                    formatted_dates += f"- {str(date_obj)}\n"
                    else:
                        # Fallback to original format
                        formatted_dates = f"- {dates_text}\n"
                except Exception as e:
                    # Fallback to original format if parsing fails
                    formatted_dates = f"- {dates_text}\n"
            else:
                formatted_dates = "- the planned dates\n"
            
            # Compose availability request message to match screenshot format
            message = f"""Hi {guest.name}! {planner.name or 'Your event planner'} wants to hang out on one of these days:

{formatted_dates.rstrip()}

Reply with your availability. You can say things like:

- 'Friday 2-6pm, Saturday after 4pm'
- 'Friday all day, Saturday evening'
- 'Friday after 3pm'"""

            # Check if guest phone number is the same as Twilio number (self-SMS prevention)
            from flask import current_app
            twilio_number = current_app.config.get('TWILIO_NUMBER')
            if twilio_number and guest.phone_number == twilio_number:
                logger.info(f"Skipping SMS to self: {guest.phone_number} (same as Twilio number)")
                # Mark as sent to avoid retries, but don't actually send
                guest.invitation_sent_at = db.func.now()
                guest.save()
                return True

            result = send_sms(guest.phone_number, message)
            
            if result['success']:
                guest.invitation_sent_at = db.func.now()
                guest.save()
                
                # Update contact's last_contacted timestamp
                if guest.contact_id:
                    contact = Contact.query.get(guest.contact_id)
                    if contact:
                        from datetime import datetime
                        contact.last_contacted = datetime.now()
                        contact.save()
                
                logger.info(f"Sent availability request to {guest.name} ({guest.phone_number})")
                return True
            else:
                logger.error(f"Failed to send availability request to {guest.phone_number}: {result.get('error')}")
                return False
            
        except Exception as e:
            logger.error(f"Error sending availability request: {e}")
            # Rollback the session in case of error
            db.session.rollback()
            return False
    
    def send_rsvp_request(self, guest: Guest, event_details: Dict[str, str]) -> bool:
        """
        Send RSVP request to a guest for a finalized event.
        
        Args:
            guest: Guest object
            event_details: Dictionary with finalized event details
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            event = guest.event
            
            # Create guest state for RSVP tracking
            guest_state = GuestState.query.filter_by(phone_number=guest.phone_number).first()
            if not guest_state:
                guest_state = GuestState(
                    phone_number=guest.phone_number,
                    current_state='awaiting_rsvp',
                    event_id=event.id
                )
            else:
                guest_state.current_state = 'awaiting_rsvp'
            
            guest_state.save()
            
            # Compose RSVP message
            message = f"""
🎉 {event.title} is confirmed!

📅 Date: {event_details.get('date', 'TBD')}
🕒 Time: {event_details.get('time', 'TBD')}
📍 Location: {event_details.get('location', 'TBD')}

Please reply with:
- YES - I'll be there
- NO - Sorry, can't make it
- MAYBE - Not sure yet

Looking forward to seeing you!
            """.strip()
            
            result = send_sms(guest.phone_number, message)
            
            if result['success']:
                logger.info(f"Sent RSVP request to {guest.name} ({guest.phone_number})")
                return True
            else:
                logger.error(f"Failed to send RSVP request to {guest.phone_number}: {result.get('error')}")
                return False
            
        except Exception as e:
            logger.error(f"Error sending RSVP request: {e}")
            return False
    
    def get_guest_summary_for_event(self, event_id: int) -> Dict[str, Any]:
        """
        Get a summary of all guests for an event.
        
        Args:
            event_id: ID of the event
            
        Returns:
            dict: Summary of guest information
        """
        try:
            guests = Guest.query.filter_by(event_id=event_id).all()
            
            summary = {
                'total_guests': len(guests),
                'rsvp_summary': {
                    'accepted': 0,
                    'declined': 0,
                    'maybe': 0,
                    'pending': 0
                },
                'availability_summary': {
                    'provided': 0,
                    'pending': 0
                },
                'guests': []
            }
            
            for guest in guests:
                # Count RSVP statuses
                summary['rsvp_summary'][guest.rsvp_status] += 1
                
                # Count availability responses
                if guest.availability_provided:
                    summary['availability_summary']['provided'] += 1
                else:
                    summary['availability_summary']['pending'] += 1
                
                # Add guest details
                summary['guests'].append({
                    'name': guest.name,
                    'phone': guest.phone_number,
                    'rsvp_status': guest.rsvp_status,
                    'availability_provided': guest.availability_provided,
                    'invitation_sent': guest.invitation_sent_at is not None
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting guest summary: {e}")
            return {
                'total_guests': 0,
                'error': str(e)
            }
