import logging
from app.handlers import BaseWorkflowHandler, HandlerResult
from app.models.event import Event
from app.models.guest import Guest
from app.models.contact import Contact

logger = logging.getLogger(__name__)

class GuestCollectionHandler(BaseWorkflowHandler):
    """Handles guest collection workflow stage"""
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            message_lower = message.lower().strip()
            
            # Handle special commands
            if message_lower in ['done', 'finished', 'next']:
                if len(event.guests) == 0:
                    return HandlerResult.error_response(
                        "You haven't added any guests yet. Please add at least one guest before proceeding."
                    )
                
                # Transition to date collection with prompt
                date_prompt = "Great! Now let's set some dates.\n\n"
                date_prompt += "When would you like to have your event?\n\n"
                date_prompt += "Examples:\n"
                date_prompt += "• 'Next Friday and Saturday'\n"
                date_prompt += "• 'December 15-17'\n"
                date_prompt += "• '8/1, 8/3, 8/5'"
                
                return HandlerResult.success_response(date_prompt, 'collecting_dates')
            
            # Handle contact selection (numeric input like "1,2,3")
            import re
            if re.match(r'^\s*\d+(\s*,\s*\d+)*\s*$', message.strip()):
                return self._handle_contact_selection(event, message)
            
            # Handle new guest addition
            result = self.guest_service.add_guests_from_text(event.id, message)
            
            if result['success']:
                guest = result['guests'][0]
                response_msg = f"Added: {guest.name} ({guest.phone_number})\n\n"
                response_msg += "Add more guests, or reply 'done' when finished."
                return HandlerResult.success_response(response_msg)
            else:
                return HandlerResult.error_response(f"❌ {result['error']}")
                
        except Exception as e:
            logger.error(f"Error in guest collection: {e}")
            return HandlerResult.error_response("Sorry, there was an error. Please try again.")
    
    def _handle_contact_selection(self, event: Event, message: str) -> HandlerResult:
        """Handle selection from previous contacts"""
        try:
            # Parse contact numbers
            if ',' in message.strip():
                selected_numbers = [int(num.strip()) for num in message.split(',')]
            else:
                selected_numbers = [int(message.strip())]
            
            # Get planner's contacts
            contacts = Contact.query.filter_by(planner_id=event.planner_id).order_by(Contact.name).all()
            
            if not contacts:
                return HandlerResult.error_response(
                    "You don't have any saved contacts yet. Please add guests with their phone numbers."
                )
            
            # Add selected contacts as guests
            added_guests = []
            for num in selected_numbers:
                if 1 <= num <= len(contacts):
                    contact = contacts[num - 1]
                    
                    # Check if already added
                    existing = Guest.query.filter_by(
                        event_id=event.id,
                        phone_number=contact.phone_number
                    ).first()
                    
                    if not existing:
                        guest = Guest(
                            event_id=event.id,
                            contact_id=contact.id,
                            name=contact.name,
                            phone_number=contact.phone_number,
                            rsvp_status='pending',
                            availability_provided=False
                        )
                        guest.save()
                        added_guests.append(guest)
            
            if added_guests:
                guest_names = [guest.name for guest in added_guests]
                response_msg = f"Added from contacts: {', '.join(guest_names)}\n\n"
                response_msg += "Add more guests or reply 'done' when finished."
                return HandlerResult.success_response(response_msg)
            else:
                return HandlerResult.error_response(
                    "Those contacts are already added or invalid numbers."
                )
                
        except ValueError:
            return HandlerResult.error_response(
                "Please use contact numbers (e.g. '1,3') or add new guests with names and phone numbers."
            )
