import logging
import re
from app.handlers import BaseWorkflowHandler, HandlerResult
from app.models.event import Event
from app.models.guest import Guest

logger = logging.getLogger(__name__)

class AddGuestsAtConfirmationHandler(BaseWorkflowHandler):
    """Handles adding guests at the confirmation stage (without sending availability requests)"""
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            message_text = message.strip()
            
            # Handle 'done' - return to confirmation menu
            if message_text.lower() == 'done':
                # Return to final confirmation with updated guest list
                confirmation_message = self.message_service.format_final_confirmation(event)
                return HandlerResult.success_response(confirmation_message, 'final_confirmation')
            
            # Parse guest information (name and phone)
            guest_info = self._parse_guest_input(message_text)
            if not guest_info:
                return HandlerResult.error_response(
                    "Please provide name and phone number.\n\n"
                    "Examples:\n"
                    "• 'John Doe, 123-456-7890'\n"
                    "• 'Mary 5105935336'\n\n"
                    "Or reply 'done' if finished adding guests."
                )
            
            name, phone = guest_info
            
            # Check if guest already exists
            existing_guest = None
            for guest in event.guests:
                if guest.phone_number == phone:
                    existing_guest = guest
                    break
            
            if existing_guest:
                return HandlerResult.error_response(
                    f"❌ {existing_guest.name} ({phone}) is already invited to this event.\n\n"
                    "Add another guest or reply 'done' if finished."
                )
            
            # Add new guest (without sending availability request)
            new_guest = Guest(
                event_id=event.id,
                name=name,
                phone_number=phone,
                rsvp_status='pending'
            )
            
            # Save the guest
            from app import db
            db.session.add(new_guest)
            db.session.commit()
            
            # Confirm addition and prompt for more
            success_message = f"✅ Added {name} to your event!\n\n"
            success_message += "Reply with another guest or 'done' if you are finished."
            
            return HandlerResult.success_response(success_message, 'adding_guests_at_confirmation')
            
        except Exception as e:
            logger.error(f"Error adding guest at confirmation: {e}")
            return HandlerResult.error_response(
                "Sorry, there was an error adding the guest. Please try again."
            )
    
    def _parse_guest_input(self, text: str) -> tuple:
        """Parse guest input to extract name and phone number"""
        # Remove extra whitespace and normalize
        text = text.strip()
        
        # Pattern 1: "Name, Phone" or "Name,Phone"
        if ',' in text:
            parts = text.split(',', 1)
            name = parts[0].strip()
            phone = self._normalize_phone(parts[1].strip())
            if name and phone:
                return name, phone
        
        # Pattern 2: "Name Phone" (space-separated)
        # Look for a phone number pattern in the text
        phone_pattern = r'(\d{3}[-.]?\d{3}[-.]?\d{4}|\d{10})'
        phone_match = re.search(phone_pattern, text)
        
        if phone_match:
            phone = self._normalize_phone(phone_match.group(1))
            # Extract name (everything before the phone number)
            name = text[:phone_match.start()].strip()
            if name and phone:
                return name, phone
        
        return None
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number format"""
        # Remove all non-digits
        digits = re.sub(r'\D', '', phone)
        
        # Add +1 if it's a 10-digit US number
        if len(digits) == 10:
            return f"+1{digits}"
        elif len(digits) == 11 and digits.startswith('1'):
            return f"+{digits}"
        
        return phone  # Return as-is if we can't normalize
