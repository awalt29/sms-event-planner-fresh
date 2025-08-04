import logging
import json
import re
from app.handlers import BaseWorkflowHandler, HandlerResult
from app.models.event import Event
from app.models.guest import Guest
from app.models.contact import Contact
from app.services.ai_processing_service import AIProcessingService

logger = logging.getLogger(__name__)

class GuestCollectionHandler(BaseWorkflowHandler):
    """Handles guest collection workflow stage"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use the AI service passed in from parent, don't create our own
    
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
            if re.match(r'^\s*\d+(\s*,\s*\d+)*\s*$', message.strip()):
                return self._handle_contact_selection(event, message)
            
            # Parse guest input using AI for this step
            guest_data = self._parse_guest_input(message)
            
            if guest_data['success']:
                added_guests = []
                for guest_info in guest_data['guests']:
                    # Add guest using existing service
                    guest = self.guest_service.add_guest_to_event(
                        event.id, 
                        guest_info['name'], 
                        guest_info.get('phone', 'N/A')
                    )
                    if guest:
                        added_guests.append(guest)
                
                if added_guests:
                    guest_names = [f"{g.name} ({g.phone_number})" for g in added_guests]
                    response = f"Added: {', '.join(guest_names)}\n\n"
                    response += "Add more guests, or reply 'done' when finished."
                    return HandlerResult.success_response(response)
            
            # If parsing failed, provide helpful error
            return HandlerResult.error_response(
                "❌ Could not parse guest information. Please use format like:\n"
                "- 'John Doe, 555-1234'\n"
                "- 'Mary 5105935336'\n"
                "- 'Sarah and Mike'"
            )
                
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

    def _parse_guest_input(self, text: str) -> dict:
        """Parse guest input specific to guest collection step"""
        logger.info(f"Guest collection - parsing input: '{text}'")
        
        # Try AI parsing first
        ai_result = self._ai_parse_guest(text)
        if ai_result and ai_result.get('success'):
            logger.info(f"Guest collection - AI parsing succeeded: {ai_result}")
            return ai_result
        
        # Fallback to regex for this step
        logger.info("Guest collection - falling back to regex parsing")
        regex_result = self._regex_parse_guest(text)
        logger.info(f"Guest collection - regex parsing result: {regex_result}")
        return regex_result
    
    def _ai_parse_guest(self, text: str) -> dict:
        """AI parsing for guest collection step only"""
        try:
            prompt = f"""Parse guest information from: "{text}"

Return JSON with:
- success: true/false
- guests: array with name and phone (phone optional)
- error: string if failed

Examples:
"John 5105935336" -> {{"success": true, "guests": [{{"name": "John", "phone": "5105935336"}}]}}
"Mary Smith, 555-1234" -> {{"success": true, "guests": [{{"name": "Mary Smith", "phone": "5551234"}}]}}
"Sarah and Mike" -> {{"success": true, "guests": [{{"name": "Sarah"}}, {{"name": "Mike"}}]}}
"hello" -> {{"success": false, "error": "No guest info found"}}"""

            logger.info(f"Guest collection - attempting AI parsing for: '{text}'")
            response = self.ai_service.make_completion(prompt, 200)
            logger.info(f"Guest collection - AI response: {response}")
            
            if response:
                result = json.loads(response)
                logger.info(f"Guest collection - AI parsing result: {result}")
                return result
                
        except Exception as e:
            logger.error(f"Guest collection AI parsing error: {e}")
            
        logger.info("Guest collection - AI parsing failed, returning None")
        return None
    
    def _regex_parse_guest(self, text: str) -> dict:
        """Regex fallback for guest collection step"""
        # Pattern: name followed by phone
        pattern = r'([A-Za-z\s]+)[\s,]+(\d{10,})'
        match = re.search(pattern, text.strip())
        
        if match:
            name = match.group(1).strip()
            phone = re.sub(r'\D', '', match.group(2))
            return {
                'success': True,
                'guests': [{'name': name, 'phone': phone}]
            }
        
        # Pattern: just names separated by "and" or comma
        name_pattern = r'([A-Za-z\s]+)(?:\s+and\s+|\s*,\s*)([A-Za-z\s]+)'
        name_match = re.search(name_pattern, text.strip())
        
        if name_match:
            names = [name_match.group(1).strip(), name_match.group(2).strip()]
            guests = [{'name': name} for name in names if name]
            return {
                'success': True,
                'guests': guests
            }
        
        # Single name
        if re.match(r'^[A-Za-z\s]+$', text.strip()):
            return {
                'success': True,
                'guests': [{'name': text.strip()}]
            }
        
        return {
            'success': False,
            'error': 'Could not parse guest information'
        }
