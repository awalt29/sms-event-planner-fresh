import logging
import re
from app.handlers import BaseWorkflowHandler, HandlerResult
from app.models.event import Event
from app.models.guest import Guest
from app.models.guest_state import GuestState
from app.models.contact import Contact

logger = logging.getLogger(__name__)

class AddGuestHandler(BaseWorkflowHandler):
    """Handles adding new guests during any workflow stage"""
    
    def __init__(self, event_service, guest_service, message_service, ai_service, availability_service):
        super().__init__(event_service, guest_service, message_service, ai_service)
        # Note: availability_service parameter kept for compatibility but not used
        # send_availability_request is in guest_service
    
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
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            message_text = message.strip().lower()
            
            # Handle 'done' - return to previous workflow stage
            if message_text == 'done':
                # Get the previous stage to return to
                previous_stage = getattr(event, 'previous_workflow_stage', 'awaiting_confirmation')
                
                if previous_stage == 'collecting_availability':
                    # Return to availability tracking - generate availability status
                    availability_msg = self.message_service.format_availability_status(event)
                    return HandlerResult.success_response(availability_msg, 'collecting_availability')
                if previous_stage == 'awaiting_confirmation':
                    # Return to awaiting_confirmation stage with updated confirmation menu
                    confirmation_msg = self.message_service.format_planner_confirmation_menu(event)
                    return HandlerResult.success_response(confirmation_msg, 'awaiting_confirmation')
                elif previous_stage == 'final_confirmation':
                    # Return to final confirmation with updated guest list
                    confirmation_msg = self.message_service.format_final_confirmation(event)
                    return HandlerResult.success_response(confirmation_msg, 'final_confirmation')
                else:
                    # Return to confirmation menu for other stages
                    confirmation_msg = self.message_service.format_planner_confirmation_menu(event)
                    return HandlerResult.success_response(confirmation_msg, previous_stage)
            
            # Handle contact selection (numeric input like "1,2,3")
            if re.match(r'^\s*\d+(\s*,\s*\d+)*\s*$', message.strip()):
                return self._handle_contact_selection(event, message)
            
            # Parse name and phone number from message
            message = ' '.join(message.split())
            
            # Extract phone number pattern
            phone_pattern = r'[\d\s\-\(\)\.]+$'
            phone_match = re.search(phone_pattern, message)
            
            if not phone_match:
                return HandlerResult.error_response(
                    "Please include both name and phone number.\n"
                    "Example: 'John Smith 555-123-4567'"
                )
            
            phone = phone_match.group().strip()
            name = message[:phone_match.start()].strip()
            
            if not name:
                return HandlerResult.error_response(
                    "Please include the guest's name.\n"
                    "Example: 'John Smith 555-123-4567'"
                )
            
            # Normalize phone number (remove non-digits)
            phone_digits = re.sub(r'\D', '', phone)
            if len(phone_digits) < 10:
                return HandlerResult.error_response(
                    "Please provide a valid 10-digit phone number."
                )
            
            # Add +1 if not present and format
            if not phone_digits.startswith('1'):
                phone_digits = '1' + phone_digits
            formatted_phone = '+' + phone_digits
            
            # Check if guest already exists
            existing_guest = Guest.query.filter_by(
                event_id=event.id,
                phone_number=formatted_phone
            ).first()
            
            if existing_guest:
                return HandlerResult.error_response(
                    f"{name} is already added to this event."
                )
            
            # Clean up any old guest states for this phone number from other events
            # to prevent conflicts when they respond to availability requests
            normalized_phone = self._normalize_phone(formatted_phone)
            old_guest_states = GuestState.query.filter(
                GuestState.phone_number.in_([formatted_phone, normalized_phone]),
                GuestState.event_id != event.id
            ).all()
            
            for old_state in old_guest_states:
                old_state.delete()
                logger.info(f"Cleaned up old guest state for {old_state.phone_number} from event {old_state.event_id}")
            
            # Create the guest
            guest = Guest(
                event_id=event.id,
                name=name,
                phone_number=formatted_phone,
                rsvp_status='pending',
                availability_provided=False
            )
            guest.save()

            # Determine return stage based on whether overlaps have been calculated
            previous_stage = getattr(event, 'previous_workflow_stage', None)
            
            # Check if overlaps have been calculated based on the PREVIOUS stage
            # These stages mean availability has been collected and overlaps calculated
            stages_with_calculated_overlaps = ['selecting_time', 'selecting_venue', 'venue_selection', 'collecting_activity', 'final_confirmation', 'finalized']
            overlaps_calculated = previous_stage in stages_with_calculated_overlaps
            
            # Debug logging
            print(f"🔍 ADD GUEST DEBUG: previous_stage={previous_stage}, event_stage={event.workflow_stage}, overlaps_calculated={overlaps_calculated}")
            logger.info(f"ADD GUEST DEBUG: previous_stage={previous_stage}, event_stage={event.workflow_stage}, overlaps_calculated={overlaps_calculated}")
            
            # Determine if we should send availability request based on the ORIGINAL stage, not current
            should_send_availability = True
            
            # Only skip availability request if we're adding guests from confirmation menu
            # or if the previous stage doesn't require availability
            if previous_stage in ['final_confirmation', 'awaiting_confirmation']:
                should_send_availability = False
                return_stage = 'adding_guest'
                # Keep previous_workflow_stage for when user says "done"
                clear_previous_stage = False
            # If we're coming from availability collection stages, always send availability request
            elif previous_stage in ['collecting_availability', 'tracking_availability', 'awaiting_availability']:
                should_send_availability = True
                return_stage = previous_stage
                clear_previous_stage = False
            # If overlaps were already calculated, we need to recalculate
            elif overlaps_calculated and previous_stage in ['selecting_time', 'selecting_venue', 'venue_selection', 'collecting_activity']:
                should_send_availability = True
                return_stage = 'collecting_availability'  # Use correct stage name
                clear_previous_stage = True
                # Clear the calculated overlaps so they'll be recalculated
                if hasattr(event, 'available_windows'):
                    event.available_windows = None
                if hasattr(event, 'selected_time'):
                    event.selected_time = None
                if hasattr(event, 'selected_venue'):
                    event.selected_venue = None
            else:
                # Default: send availability request and return to availability collection
                should_send_availability = True
                return_stage = previous_stage or 'awaiting_availability'
                clear_previous_stage = True
            
            event.workflow_stage = return_stage
            if clear_previous_stage:
                event.previous_workflow_stage = None
            event.save()
            
            # More debug logging
            print(f"🔍 ADD GUEST DEBUG: return_stage={return_stage}, should_send_availability={should_send_availability}")
            logger.info(f"ADD GUEST DEBUG: return_stage={return_stage}, should_send_availability={should_send_availability}")

            # Send availability request only if appropriate
            if should_send_availability:
                self.guest_service.send_availability_request(guest)

            # Build confirmation message
            if return_stage == 'adding_guest' and not should_send_availability:
                # Stay in adding guest mode from confirmation - don't mention availability request
                confirmation = f"✅ Added {name}!\n\n"
                
                # Show existing contacts for easy selection
                from app.models.contact import Contact
                contacts = Contact.query.filter_by(planner_id=event.planner_id).order_by(Contact.name).all()
                if contacts:
                    confirmation += "Contacts:\n"
                    for i, contact in enumerate(contacts, 1):
                        confirmation += f"{i}. {contact.name} ({contact.phone_number})\n"
                    confirmation += "\nSelect contacts (e.g. '1,3') or add new guests:\n\n"
                
                confirmation += "Add another guest or reply 'done' to continue."
            else:
                # Return to availability tracking or other workflow
                confirmation = f"✅ Added {name} to your event!\n\n"
                if should_send_availability:
                    confirmation += f"I've sent them an availability request.\n\n"
                
                # Add context-specific message
                if return_stage in ['awaiting_availability', 'collecting_availability']:
                    print(f"🔍 ADD GUEST DEBUG: Entering availability stage logic, return_stage={return_stage}")
                    logger.info(f"ADD GUEST DEBUG: Entering availability stage logic, return_stage={return_stage}")
                    # Always provide availability status for tracking stages
                    availability_status = self.message_service.format_availability_status(event)
                    print(f"🔍 ADD GUEST DEBUG: availability_status length={len(availability_status)}")
                    logger.info(f"ADD GUEST DEBUG: availability_status length={len(availability_status)}")
                    
                    if overlaps_calculated:
                        confirmation += "I'll recalculate everyone's availability once they respond.\n\n"
                        confirmation += availability_status
                        logger.info(f"ADD GUEST DEBUG: Added status with recalculation message")
                    else:
                        # Even without calculated overlaps, show status if in collecting mode
                        if return_stage == 'collecting_availability':
                            confirmation += availability_status
                            logger.info(f"ADD GUEST DEBUG: Added status for collecting_availability")
                        else:
                            confirmation += "Waiting for all guests to respond...\n\n"
                            # Still show status if there are any responses
                            responded_guests = [g for g in event.guests if g.availability_provided]
                            if responded_guests:
                                confirmation += availability_status
                                logger.info(f"ADD GUEST DEBUG: Added status because {len(responded_guests)} guests responded")
                elif return_stage == 'adding_guest':
                    # Show existing contacts for easy selection
                    from app.models.contact import Contact
                    contacts = Contact.query.filter_by(planner_id=event.planner_id).order_by(Contact.name).all()
                    if contacts:
                        confirmation += "Contacts:\n"
                        for i, contact in enumerate(contacts, 1):
                            confirmation += f"{i}. {contact.name} ({contact.phone_number})\n"
                        confirmation += "\nSelect contacts (e.g. '1,3') or add new guests:\n\n"
                    confirmation += "Add another guest or reply 'done' to continue."
            
            return HandlerResult.success_response(confirmation, return_stage)
            
        except Exception as e:
            logger.error(f"Error adding guest: {e}")
            return HandlerResult.error_response("Sorry, I couldn't add that guest. Please try again.")
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to standard format (same as SMS router)"""
        # Remove all non-digits
        digits = ''.join(filter(str.isdigit, phone))
        
        # Handle different formats
        if len(digits) == 10:
            return digits
        elif len(digits) == 11 and digits.startswith('1'):
            return digits[1:]
        
        return digits  # Return as-is if can't normalize

    def _handle_contact_selection(self, event: Event, message: str) -> HandlerResult:
        """Handle selection from previous contacts (reused from guest collection handler)"""
        try:
            # Parse contact numbers
            if ',' in message.strip():
                selected_numbers = [int(num.strip()) for num in message.split(',')]
            else:
                selected_numbers = [int(message.strip())]
            
            # Get planner's contacts
            from app.models.contact import Contact
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
                        
                        # Send availability request if appropriate
                        previous_stage = getattr(event, 'previous_workflow_stage', None)
                        stages_with_calculated_overlaps = ['selecting_time', 'selecting_venue', 'venue_selection', 'collecting_activity', 'final_confirmation', 'finalized']
                        should_send_availability = previous_stage not in ['final_confirmation', 'awaiting_confirmation']
                        
                        if should_send_availability:
                            self.guest_service.send_availability_request(guest)
            
            if added_guests:
                guest_names = [guest.name for guest in added_guests]
                response_msg = f"✅ Added: {', '.join(guest_names)}\n\n"
                
                # Show current guest list
                response_msg += self._generate_guest_list_display(event)
                
                # Show updated contact list so users can continue adding
                if contacts:
                    response_msg += "Select contacts (e.g. '1,3') or add new guests:\n\n"
                    response_msg += "Contacts:\n"
                    for i, contact in enumerate(contacts, 1):
                        response_msg += f"{i}. {contact.name} ({contact.phone_number})\n"
                    response_msg += "\n"
                
                response_msg += "Add another guest or reply 'done' to continue."
                return HandlerResult.success_response(response_msg)
            else:
                return HandlerResult.error_response(
                    "Those contacts are already added or invalid numbers."
                )
                
        except ValueError:
            return HandlerResult.error_response(
                "Please use contact numbers (e.g. '1,3') or add new guests with names and phone numbers."
            )
