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
                    # Validate that guest has phone number
                    if not guest_info.get('phone'):
                        return HandlerResult.error_response(
                            "❌ All guests must have phone numbers. Please include phone numbers for all guests."
                        )
                    
                    # Add guest using existing service
                    guest = self.guest_service.add_guest_to_event(
                        event.id, 
                        guest_info['name'], 
                        guest_info['phone']
                    )
                    if guest:
                        added_guests.append(guest)
                
                if added_guests:
                    guest_names = [f"{g.name} ({g.phone_number})" for g in added_guests]
                    response = f"✅ Added: {', '.join(guest_names)}\n\n"
                    
                    # Show current guest list
                    response += self._generate_guest_list_display(event)
                    
                    # Show updated contact list so users can continue adding
                    response += self._generate_contact_list_display(event)
                    response += "Add more guests, or reply 'done' when finished."
                    return HandlerResult.success_response(response)
            
            # If parsing failed, provide helpful error
            return HandlerResult.error_response(
                "❌ Could not parse guest information. Please use format like:\n"
                "- 'John Doe, 111-555-1234'\n"
                "- 'Mary 5105935336'"
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
                response_msg = f"✅ Added: {', '.join(guest_names)}\n\n"
                
                # Show current guest list
                response_msg += self._generate_guest_list_display(event)
                
                # Show updated contact list so users can continue adding
                response_msg += self._generate_contact_list_display(event)
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
- guests: array with name and phone (phone REQUIRED)
- error: string if failed

IMPORTANT: All guests must have phone numbers. Reject inputs without phone numbers.

PHONE NUMBER FORMATS TO ACCEPT:
- Standard: "John 5105935336", "Mary Smith 111-555-1234"
- With parentheses: "Aaron(9145606464)", "Sarah(555) 123-4567"
- With formatting: "Mike (555) 123-4567", "Lisa 555.123.4567"
- Various separators: "Tom,5551234567", "Jane - 555-1234"
- Mixed formats: "Bob Smith(555)1234567", "Alice:555-123-4567"

EXTRACT PHONE NUMBERS FROM:
- Numbers in parentheses: Aaron(9145606464) -> name="Aaron", phone="9145606464"
- Numbers with dashes: John 555-123-4567 -> name="John", phone="5551234567"
- Numbers with spaces: Mary 555 123 4567 -> name="Mary", phone="5551234567"
- Numbers with dots: Tom 555.123.4567 -> name="Tom", phone="5551234567"

Examples:
"John 5105935336" -> {{"success": true, "guests": [{{"name": "John", "phone": "5105935336"}}]}}
"Aaron(9145606464)" -> {{"success": true, "guests": [{{"name": "Aaron", "phone": "9145606464"}}]}}
"Mary Smith, 111-555-1234" -> {{"success": true, "guests": [{{"name": "Mary Smith", "phone": "1115551234"}}]}}
"Bob(555) 123-4567" -> {{"success": true, "guests": [{{"name": "Bob", "phone": "5551234567"}}]}}
"Sarah and Mike" -> {{"success": false, "error": "Phone numbers required for all guests"}}
"hello" -> {{"success": false, "error": "No guest info found"}}"""

            logger.info(f"Guest collection - attempting AI parsing for: '{text}'")
            response = self.ai_service.make_completion(prompt, 200)
            logger.info(f"Guest collection - AI response: {response}")
            
            if response and response.strip():
                try:
                    # Extract JSON from response - AI sometimes adds markdown formatting
                    import re
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        result = json.loads(json_str)
                        logger.info(f"Guest collection - AI parsing result: {result}")
                        return result
                    else:
                        logger.error(f"Guest collection - No JSON found in AI response: '{response}'")
                except json.JSONDecodeError as je:
                    logger.error(f"Guest collection - JSON parsing error: {je}, Response: '{response}'")
            else:
                logger.error(f"Guest collection - AI returned empty/None response for input: '{text}'")
                
        except Exception as e:
            logger.error(f"Guest collection AI parsing error: {e}")
            
        logger.info("Guest collection - AI parsing failed, returning None")
        return None
    
    def _regex_parse_guest(self, text: str) -> dict:
        """Regex fallback for guest collection step - requires phone numbers"""
        import re
        
        # Enhanced patterns to handle various phone number formats
        patterns = [
            # Name with phone in parentheses: Aaron(9145606464), Bob(555) 123-4567, Mike(555)1234567
            r'([A-Za-z\s]+)\(([0-9\-\(\)\s\.]+)\)([0-9\-\s]*)',
            
            # Name with phone in parentheses (simple): Aaron(9145606464)
            r'([A-Za-z\s]+)\(([0-9]+)\)',
            
            # Standard: name followed by phone with separator: John Smith, 555-1234
            r'([A-Za-z\s]+)[\s,:\-]+([0-9\-\(\)\s\.]{10,})',
            
            # Name followed by phone with minimal separator: John 5551234567
            r'([A-Za-z\s]+)\s+([0-9\-\(\)\s\.]{10,})',
            
            # Phone number first: 555-1234 John Smith
            r'([0-9\-\(\)\s\.]{10,})[\s,:\-]+([A-Za-z\s]+)'
        ]
        
        text = text.strip()
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                # For patterns with 3 groups (parentheses with additional numbers)
                if len(match.groups()) == 3:
                    name = match.group(1).strip()
                    phone_part1 = re.sub(r'\D', '', match.group(2))
                    phone_part2 = re.sub(r'\D', '', match.group(3)) if match.group(3) else ''
                    phone = phone_part1 + phone_part2
                else:
                    # For patterns where phone might be first, check which group has digits
                    group1 = match.group(1).strip()
                    group2 = match.group(2).strip()
                    
                    # Extract digits from both groups to determine which is the phone
                    digits1 = re.sub(r'\D', '', group1)
                    digits2 = re.sub(r'\D', '', group2)
                    
                    # Determine name and phone based on which has more digits
                    if len(digits2) >= 10 and len(digits1) < len(digits2):
                        name = group1
                        phone = digits2
                    elif len(digits1) >= 10 and len(digits2) < len(digits1):
                        name = group2
                        phone = digits1
                    elif len(digits2) >= 10:  # Default to second group as phone
                        name = group1
                        phone = digits2
                    elif len(digits1) >= 10:  # Fallback to first group as phone
                        name = group2
                        phone = digits1
                    else:
                        continue  # Neither group has enough digits
                
                # Clean up name (remove extra spaces)
                name = re.sub(r'\s+', ' ', name).strip()
                
                # Validate phone number length
                if len(phone) >= 10:
                    return {
                        'success': True,
                        'guests': [{'name': name, 'phone': phone}]
                    }
        
        # If no valid pattern found, reject the input
        return {
            'success': False,
            'error': 'Phone number required for all guests'
        }
    
    def _generate_guest_list_display(self, event: Event) -> str:
        """Generate current guest list display"""
        guests = event.guests
        if guests:
            display = "Guest list:\n"
            for guest in guests:
                display += f"- {guest.name}\n"
            display += "\n"
            return display
        return "Guest list: (none yet)\n\n"
    
    def _generate_contact_list_display(self, event: Event) -> str:
        """Generate contact list display for reuse"""
        contacts = Contact.query.filter_by(planner_id=event.planner_id).order_by(Contact.name).all()
        if contacts:
            display = "Select contacts (e.g. '1,3') or add new guests (e.g. 'John Doe, 123-456-7890').\n\n"
            display += "Contacts:\n"
            for i, contact in enumerate(contacts, 1):
                display += f"{i}. {contact.name} ({contact.phone_number})\n"
            display += "\n"
            return display
        return ""
