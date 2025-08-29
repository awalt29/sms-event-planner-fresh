from flask import Blueprint, request
from twilio.twiml.messaging_response import MessagingResponse
import logging
from app.models.planner import Planner
from app.models.event import Event
from app.models.guest import Guest
from app.models.guest_state import GuestState
from app.models.contact import Contact
from app.services import (
    EventWorkflowService,
    GuestManagementService, 
    MessageFormattingService,
    AIProcessingService,
    VenueService,
    AvailabilityService
)
from app.handlers.guest_collection_handler import GuestCollectionHandler
from app.handlers.date_collection_handler import DateCollectionHandler
from app.handlers.confirmation_menu_handler import ConfirmationMenuHandler
from app.handlers.availability_tracking_handler import AvailabilityTrackingHandler

logger = logging.getLogger(__name__)
sms_bp = Blueprint("sms", __name__)

class SMSRouter:
    """Routes SMS messages to appropriate handlers"""
    
    def __init__(self):
        # PERFORMANCE OPTIMIZATION: Use singleton services to avoid recreating
        # services for every SMS message. This reduces initialization overhead
        # from ~75ms to ~5ms per message.
        from app.services.service_manager import get_shared_services
        
        (self.event_service, 
         self.guest_service, 
         self.message_service, 
         self.ai_service, 
         self.venue_service, 
         self.availability_service) = get_shared_services()
        
        # PERFORMANCE OPTIMIZATION: Data integrity service removed from SMS router
        # Background integrity checks now handled separately to avoid blocking SMS processing
        
        # Initialize handlers
        # Import handlers
        from app.handlers.guest_collection_handler import GuestCollectionHandler
        from app.handlers.date_collection_handler import DateCollectionHandler
        from app.handlers.confirmation_menu_handler import ConfirmationMenuHandler
        from app.handlers.availability_tracking_handler import AvailabilityTrackingHandler
        from app.handlers.guest_availability_handler import GuestAvailabilityHandler
        from app.handlers.time_selection_handler import TimeSelectionHandler
        from app.handlers.partial_time_selection_handler import PartialTimeSelectionHandler
        from app.handlers.location_collection_handler import LocationCollectionHandler
        from app.handlers.activity_collection_handler import ActivityCollectionHandler
        from app.handlers.venue_selection_handler import VenueSelectionHandler
        from app.handlers.final_confirmation_handler import FinalConfirmationHandler
        from app.handlers.start_time_setting_handler import StartTimeSettingHandler
        from app.handlers.add_guest_handler import AddGuestHandler
        from app.handlers.remove_contact_handler import RemoveContactHandler
        from app.handlers.contact_removal_handler import ContactRemovalHandler
        
        # Initialize guest availability handler
        self.guest_availability_handler = GuestAvailabilityHandler(
            self.event_service, self.guest_service,
            self.message_service, self.ai_service
        )
        
        self.handlers = {
            'collecting_guests': GuestCollectionHandler(
                self.event_service, self.guest_service,
                self.message_service, self.ai_service
            ),
            'collecting_dates': DateCollectionHandler(
                self.event_service, self.guest_service,
                self.message_service, self.ai_service
            ),
            'awaiting_confirmation': ConfirmationMenuHandler(
                self.event_service, self.guest_service,
                self.message_service, self.ai_service
            ),
            'collecting_availability': AvailabilityTrackingHandler(
                self.event_service, self.guest_service,
                self.message_service, self.ai_service
            ),
            'selecting_time': TimeSelectionHandler(
                self.event_service, self.guest_service,
                self.message_service, self.ai_service
            ),
            'selecting_partial_time': PartialTimeSelectionHandler(
                self.event_service, self.guest_service,
                self.message_service, self.ai_service
            ),
            'collecting_location': LocationCollectionHandler(
                self.event_service, self.guest_service,
                self.message_service, self.ai_service
            ),
            'collecting_activity': ActivityCollectionHandler(
                self.event_service, self.guest_service,
                self.message_service, self.ai_service, self.venue_service
            ),
            'selecting_venue': VenueSelectionHandler(
                self.event_service, self.guest_service,
                self.message_service, self.ai_service, self.venue_service
            ),
            'final_confirmation': FinalConfirmationHandler(
                self.event_service, self.guest_service,
                self.message_service, self.ai_service
            ),
            'setting_start_time': StartTimeSettingHandler(
                self.event_service, self.guest_service,
                self.message_service, self.ai_service
            ),
            'adding_guest': AddGuestHandler(
                self.event_service, self.guest_service,
                self.message_service, self.ai_service, self.availability_service
            ),
            'removing_contact': ContactRemovalHandler()
        }
    
    def route_message(self, phone_number: str, message: str) -> str:
        """Main routing logic - everyone is a planner by default, guest mode per-message only"""
        try:
            # PERFORMANCE OPTIMIZATION: Data integrity checks moved to background
            # Original blocking integrity check code removed - now handled by background job
            # This eliminates 200-500ms periodic delays in SMS processing
            
            # Normalize phone number
            normalized_phone = self._normalize_phone(phone_number)
            logger.info(f"SMS Router - Original phone: {phone_number}, Normalized: {normalized_phone}")
            
            # Check if they're temporarily responding to an invitation/availability request
            guest_state = GuestState.query.filter_by(phone_number=normalized_phone).first()
            logger.info(f"SMS Router - Guest state found: {guest_state is not None}")
            if guest_state:
                logger.info(f"SMS Router - Guest state: {guest_state.current_state}")
            
            if guest_state:
                # Handle as guest (temporary override for responding to invitations)
                response = self._handle_guest_message(guest_state, message)
                
                # Only cleanup guest state if marked as completed
                updated_guest_state = GuestState.query.filter_by(phone_number=normalized_phone).first()
                if updated_guest_state and updated_guest_state.current_state == 'completed':
                    self._cleanup_guest_state(updated_guest_state)
                
                return response
            
            # Default: Handle as planner (everyone is a planner unless responding to invitations)
            planner = self._get_or_create_planner(normalized_phone)
            return self._handle_planner_message(planner, message)
            
        except Exception as e:
            logger.error(f"Error routing message: {e}")
            return self._create_error_response()
    
    def _handle_planner_message(self, planner: Planner, message: str) -> str:
        """Handle messages from planners"""
        try:
            # Get active event first to check workflow stage
            active_event = self._get_active_event(planner.id)
            logger.info(f"Planner {planner.id} active event: {active_event.id if active_event else None}")
            
            # Check if we're in name collection stage FIRST - new planners must provide name before any other commands
            if active_event and active_event.workflow_stage == 'waiting_for_name':
                logger.info(f"Event {active_event.id} waiting for name - asking for name")
                # Update stage to indicate we've asked for the name
                active_event.workflow_stage = 'collecting_name'
                active_event.save()
                return "🎉 Welcome to Gatherly!\n\n What's your name?"
            elif active_event and active_event.workflow_stage == 'collecting_name':
                logger.info(f"Event {active_event.id} in name collection stage - processing name")
                return self._handle_name_collection(planner, message)
            
            # Check if name is needed (fallback for old planners without the new workflow)
            if not planner.name:
                logger.info(f"Planner {planner.id} needs name, handling name collection")
                return self._handle_name_collection(planner, message)
            
            # Only AFTER name is collected, handle other commands like reset
            if message.lower().strip() in ['reset', 'restart', 'start over']:
                logger.info(f"Processing reset command for planner {planner.id}")
                return self._handle_reset_command(planner)
            
            if active_event:
                logger.info(f"Processing workflow message for event {active_event.id}")
                return self._handle_workflow_message(active_event, message)
            else:
                logger.info(f"No active event, handling new event request with message: '{message}'")
                return self._handle_new_event_request(planner, message)
                
        except Exception as e:
            logger.error(f"Error handling planner message: {e}")
            return self._create_error_response()
    
    def _handle_workflow_message(self, event: Event, message: str) -> str:
        """Route message to appropriate workflow handler"""
        try:
            message_lower = message.lower().strip()
            
            # Check for global commands that work at any workflow stage (only for named planners)
            # But let confirmation handlers process "3" and "add guests" first
            # Skip if at final_confirmation stage or if previous stage was awaiting_confirmation
            previous_stage = getattr(event, 'previous_workflow_stage', None)
            if message_lower in ['add guest', 'add guests'] and event.workflow_stage not in ['final_confirmation'] and previous_stage != 'awaiting_confirmation':
                return self._handle_add_guest_request(event)
            
            if message_lower in ['remove contact', 'remove contacts']:
                return self._handle_remove_contact_request(event)
            
            handler = self.handlers.get(event.workflow_stage)
            
            if handler:
                result = handler.handle_message(event, message)
                
                # Handle stage transitions
                if result.next_stage:
                    event.workflow_stage = result.next_stage
                    event.save()
                
                return result.message
            else:
                logger.warning(f"No handler for stage: {event.workflow_stage}")
                return self._create_error_response("I'm not sure how to help with that right now.")
                
        except Exception as e:
            logger.error(f"Error in workflow handling: {e}")
            return self._create_error_response()
    
    def _handle_guest_message(self, guest_state: GuestState, message: str) -> str:
        """Handle messages from guests with active states - single response per state"""
        try:
            current_state = guest_state.current_state
            
            if current_state == 'awaiting_availability':
                return self._handle_availability_response(guest_state, message)
            elif current_state == 'awaiting_preferences':
                # Handle preferences workflow - delegate to availability handler
                return self._handle_availability_response(guest_state, message)
            elif current_state == 'awaiting_rsvp':
                return self._handle_rsvp_response(guest_state, message)
            elif current_state == 'completed':
                # Guest session is complete, clean up and redirect to planner mode
                return self._cleanup_guest_state_and_redirect(guest_state)
            else:
                # Unknown state - log error but don't cleanup, let the handler decide
                logger.error(f"Unknown guest state: {current_state} for phone {guest_state.phone_number}")
                return self._handle_availability_response(guest_state, message)
                
        except Exception as e:
            logger.error(f"Error handling guest message: {e}")
            return self._create_error_response()
    
    def _handle_availability_response(self, guest_state: GuestState, message: str) -> str:
        """Handle guest availability response - delegate to proper handler"""
        return self.guest_availability_handler.handle_availability_response(guest_state, message)
    
    def _handle_rsvp_response(self, guest_state: GuestState, message: str) -> str:
        """Handle guest RSVP response - single message, immediate cleanup"""
        try:
            message_lower = message.lower().strip()
            
            # Find the guest record - try multiple phone number formats
            from app.models.guest import Guest
            
            # Try the exact phone number from guest_state first
            guest = Guest.query.filter_by(
                event_id=guest_state.event_id,
                phone_number=guest_state.phone_number
            ).first()
            
            # If not found, try with +1 prefix (common format mismatch)
            if not guest:
                prefixed_phone = f"+1{guest_state.phone_number}"
                guest = Guest.query.filter_by(
                    event_id=guest_state.event_id,
                    phone_number=prefixed_phone
                ).first()
            
            # If still not found, try with just + prefix
            if not guest:
                plus_phone = f"+{guest_state.phone_number}"
                guest = Guest.query.filter_by(
                    event_id=guest_state.event_id,
                    phone_number=plus_phone
                ).first()
            
            if guest:
                if message_lower in ['yes', 'y']:
                    guest.rsvp_status = 'yes'
                    response_text = "🎉 Great! You're confirmed for the event."
                elif message_lower in ['no', 'n']:
                    guest.rsvp_status = 'no'
                    response_text = "Thanks for letting us know. You'll be missed!"
                elif message_lower in ['maybe', 'm']:
                    guest.rsvp_status = 'maybe'
                    response_text = "Got it! Marked as maybe. Hope you can make it!"
                else:
                    return "Please reply 'Yes', 'No', or 'Maybe' to confirm your attendance."
                
                guest.save()
                
                # Send notification to planner about RSVP response
                self._send_rsvp_notification_to_planner(guest, guest_state)
                
                # Mark guest state for cleanup - RSVP is complete
                guest_state.current_state = 'completed'
                guest_state.save()
                
                return response_text
            
            return self._create_error_response("Sorry, there was an error processing your RSVP.")
            
        except Exception as e:
            logger.error(f"Error handling RSVP response: {e}")
            return self._create_error_response("Sorry, there was an error processing your RSVP.")
    
    def _handle_name_collection(self, planner: Planner, message: str) -> str:
        """Handle initial name collection for new planners"""
        name = message.strip()
        
        # Reject common commands that shouldn't be treated as names
        if name.lower() in ['reset', 'restart', 'start over', 'add guest', 'add guests', 'remove contact', 'remove contacts', 'done', 'help']:
            return "Please tell me your name first so I can help you plan your event!"
        
        if len(name) > 0:
            planner.name = name
            planner.save()
            
            # Update the placeholder event to move to guest collection
            event = Event.query.filter_by(planner_id=planner.id, status='planning').first()
            if event:
                event.workflow_stage = 'collecting_guests'
                event.save()
            
            # Check for existing contacts to show proper messaging
            contacts = Contact.query.filter_by(planner_id=planner.id).order_by(Contact.name).all()
            
            welcome_text = f"Great to meet you, {name}! 👋\n"
            welcome_text += "Let's plan your event!\n\n"
            welcome_text += "Who's coming?\n\n"
            
            if contacts:
                welcome_text += "Contacts:\n"
                for i, contact in enumerate(contacts, 1):
                    welcome_text += f"{i}. {contact.name} ({contact.phone_number})\n"
                welcome_text += "\nSelect contacts (e.g. '1,3') or add new guests (e.g. 'John Doe, 123-456-7890').\n\n"
            else:
                welcome_text += "Add guests as: Name, Phone\n"
                welcome_text += "(E.g., John Doe, 123-456-7890)\n\n"
            
            welcome_text += "Add one guest at a time.\n\n"
            welcome_text += "Say 'Restart' to start over at any time"
            
            return welcome_text
        else:
            return "Please tell me your name so I can help you plan your event!"
    
    def _send_rsvp_notification_to_planner(self, guest: Guest, guest_state: GuestState) -> None:
        """Send notification to planner when guest responds to RSVP"""
        try:
            event = guest_state.event
            planner = event.planner
            guest_name = guest.name
            rsvp_status = guest.rsvp_status
            
            # Count RSVP responses
            total_guests = Guest.query.filter_by(event_id=event.id).count()
            responded_guests = Guest.query.filter_by(event_id=event.id).filter(
                Guest.rsvp_status.in_(['yes', 'no', 'maybe'])
            ).count()
            pending_guests = total_guests - responded_guests
            
            # Format RSVP status with emoji
            status_emoji = {
                'yes': '👍',
                'no': '❌', 
                'maybe': '🤔'
            }
            
            status_text = {
                'yes': 'is going',
                'no': 'declined',
                'maybe': 'responded maybe'
            }
            
            # Create planner notification message
            planner_message = f"{status_emoji.get(rsvp_status, '📝')} {guest_name} {status_text.get(rsvp_status, 'responded')}!\n\n"
            planner_message += f"📊 {responded_guests}/{total_guests} guests have responded\n"
            
            if pending_guests > 0:
                planner_message += f"⏳ Waiting for {pending_guests} more guest" + ("s" if pending_guests != 1 else "")
            else:
                planner_message += "🎉 Everyone has responded to your event!"
            
            # Send SMS to planner
            from app.services.sms_service import SMSService
            sms_service = SMSService()
            sms_service.send_sms(planner.phone_number, planner_message)
            logger.info(f"Sent RSVP notification to planner {planner.phone_number} about {guest_name}'s response: {rsvp_status}")
            
        except Exception as e:
            logger.error(f"Error sending RSVP notification to planner: {e}")

    def _handle_add_guest_request(self, event: Event) -> str:
        """Handle global add guest request"""
        try:
            # Check if we're in an early stage where adding guests would disrupt the flow
            early_stages = ['collecting_guests', 'collecting_dates', 'awaiting_confirmation']
            if event.workflow_stage in early_stages:
                if event.workflow_stage == 'collecting_dates':
                    return "Let's finish setting your event dates first!\n\nWhen would you like to have your event?\n\nExamples:\n- 'Next Friday and Saturday'\n- 'December 15-17'\n- '8/1, 8/3, 8/5'"
                elif event.workflow_stage == 'collecting_guests':
                    return "👥 Let's finish adding your initial guest list first, then you can add more guests later during planning.\n\nWho else would you like to invite?"
                else:  # awaiting_confirmation
                    return "📋 You can add more guests after we start collecting availability. Let's confirm your event details first!"
            
            add_guest_prompt = "Who would you like to add to this event?\n\n"
            add_guest_prompt += "Send me their name and phone number:\n"
            add_guest_prompt += "• 'John Smith 555-123-4567'\n"
            add_guest_prompt += "• 'Sarah (555) 987-6543'"

            # Store current stage to return to after adding guest
            event.previous_workflow_stage = event.workflow_stage
            event.workflow_stage = 'adding_guest'
            event.save()
            
            return add_guest_prompt
            
        except Exception as e:
            logger.error(f"Error handling add guest request: {e}")
            return "Sorry, I couldn't process your request. Please try again."
    
    def _handle_remove_contact_request(self, event: Event) -> str:
        """Handle global remove contact request"""
        try:
            from app.handlers.remove_contact_handler import RemoveContactHandler
            
            remove_contact_handler = RemoveContactHandler()
            result = remove_contact_handler.handle_message(event, "remove contact")
            
            if result.success:
                # Update event workflow stage if handler changed it
                if result.next_stage:
                    event.workflow_stage = result.next_stage
                    event.save()
                return result.message
            else:
                return result.message
            
        except Exception as e:
            logger.error(f"Error handling remove contact request: {e}")
            return "Sorry, I couldn't process your request. Please try again."

    def _handle_reset_command(self, planner: Planner) -> str:
        """Handle reset/restart commands"""
        logger.info(f"Reset command called for planner {planner.id} ({planner.phone_number})")
        
        # Cancel any active events
        active_events = Event.query.filter_by(
            planner_id=planner.id,
            status='planning'
        ).all()
        
        logger.info(f"Reset command: Found {len(active_events)} active events for planner {planner.id}")
        
        for event in active_events:
            logger.info(f"Cancelling event {event.id} (stage: {event.workflow_stage})")
            event.status = 'cancelled'
            event.save()
            logger.info(f"Event {event.id} cancelled successfully")
        
        # Create a new fresh event and go directly to guest collection
        new_event = Event(
            planner_id=planner.id,
            workflow_stage='collecting_guests',
            status='planning'
        )
        new_event.save()
        logger.info(f"Created new event {new_event.id} in {new_event.workflow_stage} stage for planner {planner.id}")
        
        # Check for existing contacts to show (same logic as new event creation)
        contacts = Contact.query.filter_by(planner_id=planner.id).order_by(Contact.name).all()
        
        welcome_text = "Let's plan your event!\n\n"
        welcome_text += "Who's coming?\n\n"
        
        if contacts:
            welcome_text += "Contacts:\n"
            for i, contact in enumerate(contacts, 1):
                welcome_text += f"{i}. {contact.name} ({contact.phone_number})\n"
            welcome_text += "\nSelect contacts (e.g. '1,3') or add new guests (e.g. 'John Doe, 123-456-7890').\n\n"
        else:
            welcome_text += "Add guests as: Name, Phone\n"
            welcome_text += "(E.g., John Doe, 123-456-7890)\n\n"
        
        welcome_text += "Add one guest at a time.\n\n"
        welcome_text += "💡 Commands:\n"
        welcome_text += "- 'Remove contact'\n"
        welcome_text += "- 'Restart'"
        
        return welcome_text
    
    def _handle_new_event_request(self, planner: Planner, message: str) -> str:
        """Handle new event creation requests"""
        logger.info(f"Handling new event request for planner {planner.id} with message: '{message}'")
        
        # Check if this looks like guest input (name + phone pattern)
        if self._looks_like_guest_input(message):
            logger.info(f"Message looks like guest input, calling _handle_guest_input_without_event")
            # Create a simple default event and process as guest input
            return self._handle_guest_input_without_event(planner, message)
        
        logger.info(f"Message looks like event description, creating event from text")
        # Otherwise treat as event description
        result = self.event_service.create_event_from_text(planner.id, message)
        
        if result['success']:
            event = result['event']
            
            # Check for existing contacts to show
            contacts = Contact.query.filter_by(planner_id=planner.id).order_by(Contact.name).all()
            
            response_text = "Who's coming to your event?\n\n"
            
            if contacts:
                response_text += "Contacts:\n"
                for i, contact in enumerate(contacts, 1):
                    response_text += f"{i}. {contact.name} ({contact.phone_number})\n"
                response_text += "\nSelect contacts (e.g. '1,3') or add new guests (e.g. 'John Doe, 123-456-7890').\n\n"
            else:
                response_text += "Add guests as: Name, Phone\n"
                response_text += "(E.g., John Doe, 123-456-7890)\n\n"
                
                response_text += "Add one guest at a time.\n\n"
                response_text += "💡 Commands:\n"
                response_text += "- 'Remove contact'\n"
                response_text += "- 'Restart'"
            
            
            return response_text
        else:
            return f"Sorry, I couldn't create your event. {result.get('error', 'Please try again.')}"
    
    def _get_or_create_planner(self, phone_number: str) -> Planner:
        """Get existing planner or create new one"""
        planner = Planner.query.filter_by(phone_number=phone_number).first()
        
        if not planner:
            planner = Planner(phone_number=phone_number)
            planner.save()
            
            # Create a placeholder event in name collection stage
            event = Event(
                planner_id=planner.id,
                workflow_stage='waiting_for_name',
                status='planning'
            )
            event.save()
        
        return planner
    
    def _get_active_event(self, planner_id: int) -> Event:
        """Get active event for planner"""
        return Event.query.filter_by(
            planner_id=planner_id,
            status='planning'
        ).first()
    
    def _cleanup_guest_state(self, guest_state: GuestState):
        """Clean up guest state - return to planner mode"""
        try:
            guest_state.delete()
        except Exception as e:
            logger.error(f"Error cleaning up guest state: {e}")
    
    def _cleanup_guest_state_and_redirect(self, guest_state: GuestState) -> str:
        """Clean up guest state and redirect to planner mode"""
        planner = self._get_or_create_planner(guest_state.phone_number)
        self._cleanup_guest_state(guest_state)
        return self._handle_planner_message(planner, "")
    
    def _looks_like_guest_input(self, message: str) -> bool:
        """Check if message looks like guest input (name + phone pattern)"""
        import re
        
        # Look for patterns like "Name Phone" or "Name, Phone"
        guest_patterns = [
            r'^[A-Za-z\s]+\s+[\d\-\(\)\s]{10,}$',  # "John Doe 1234567890"
            r'^[A-Za-z\s]+,\s*[\d\-\(\)\s]{10,}$', # "John Doe, 123-456-7890"
            r'^[A-Za-z\s]+\s+\(\d{3}\)\s*\d{3}-\d{4}$',  # "John Doe (123) 456-7890"
        ]
        
        for pattern in guest_patterns:
            if re.match(pattern, message.strip()):
                return True
        
        return False
    
    def _handle_guest_input_without_event(self, planner: Planner, message: str) -> str:
        """Handle guest input when no active event exists - create simple event and process guest"""
        try:
            # Create a simple default event
            event = Event(
                planner_id=planner.id,
                title="My Event",
                workflow_stage='collecting_guests',
                status='planning'
            )
            event.save()
            logger.info(f"Created default event {event.id} for guest input processing")
            
            # Verify event was saved
            saved_event = Event.query.get(event.id)
            if not saved_event:
                logger.error(f"Event {event.id} not found after save!")
                return self._create_error_response("Sorry, I couldn't create an event.")
            
            logger.info(f"Event {event.id} confirmed saved, processing guest input: '{message}'")
            
            # Now process the guest input using the guest collection handler
            handler = self.handlers.get('collecting_guests')
            if handler:
                result = handler.handle_message(event, message)
                
                # Verify the results were saved
                contacts_after = Contact.query.filter_by(planner_id=planner.id).all()
                guests_after = event.guests
                logger.info(f"After handler - Contacts: {len(contacts_after)}, Guests: {len(guests_after)}")
                
                if result.next_stage:
                    event.workflow_stage = result.next_stage
                    event.save()
                    logger.info(f"Updated event {event.id} to stage: {result.next_stage}")
                
                return result.message
            else:
                logger.error("No guest collection handler available")
                return self._create_error_response("Sorry, I couldn't process that guest information.")
                
        except Exception as e:
            logger.error(f"Error handling guest input without event: {e}", exc_info=True)
            return self._create_error_response()
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to standard format"""
        # Remove all non-digits
        digits = ''.join(filter(str.isdigit, phone))
        
        # Handle different formats
        if len(digits) == 10:
            return digits
        elif len(digits) == 11 and digits.startswith('1'):
            return digits[1:]
        
        return digits  # Return as-is if can't normalize
    
    def _create_error_response(self, message: str = "Sorry, there was an error. Please try again.") -> str:
        """Create standardized error response"""
        return message

# Initialize router
router = SMSRouter()

@sms_bp.route('/webhook', methods=['POST'])
def sms_webhook():
    """Handle incoming SMS messages"""
    try:
        # Get message data from Twilio
        from_number = request.form.get('From', '').replace('+1', '')
        message_body = request.form.get('Body', '').strip()
        
        logger.info(f"SMS webhook - From: '{from_number}', Body: '{message_body}' (length: {len(message_body)})")
        
        if not from_number or not message_body:
            logger.error("Missing phone number or message body")
            return str(MessagingResponse())
        
        # PERFORMANCE MONITORING: Track SMS response times
        import time
        start_time = time.time()
        
        # Route message and get response
        response_text = router.route_message(from_number, message_body)
        
        # Log performance metrics
        processing_time = time.time() - start_time
        logger.info(f"SMS processed in {processing_time:.3f}s - Response length: {len(response_text)}")
        
        # Create Twilio response
        resp = MessagingResponse()
        resp.message(response_text)
        
        return str(resp)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error in SMS webhook: {e}")
        logger.error(f"Full traceback: {error_details}")
        resp = MessagingResponse()
        resp.message("Sorry, there was an error processing your message. Please try again.")
        return str(resp)

@sms_bp.route('/test', methods=['POST'])
def test_sms():
    """Test endpoint for development"""
    try:
        data = request.get_json()
        phone_number = data.get('phone_number', '1234567890')
        message = data.get('message', 'test')
        
        response = router.route_message(phone_number, message)
        
        return {'response': response}, 200
        
    except Exception as e:
        logger.error(f"Error in test endpoint: {e}")
        return {'error': str(e)}, 500
