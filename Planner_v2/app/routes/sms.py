from flask import Blueprint, request
from twilio.twiml.messaging_response import MessagingResponse
import logging
from app.models.planner import Planner
from app.models.event import Event
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
        # Initialize services
        self.event_service = EventWorkflowService()
        self.guest_service = GuestManagementService()
        self.message_service = MessageFormattingService()
        self.ai_service = AIProcessingService()
        self.venue_service = VenueService()
        self.availability_service = AvailabilityService()
        
        # Initialize handlers
        # Import handlers
        from app.handlers.guest_collection_handler import GuestCollectionHandler
        from app.handlers.date_collection_handler import DateCollectionHandler
        from app.handlers.confirmation_menu_handler import ConfirmationMenuHandler
        from app.handlers.availability_tracking_handler import AvailabilityTrackingHandler
        from app.handlers.time_selection_handler import TimeSelectionHandler
        from app.handlers.location_collection_handler import LocationCollectionHandler
        from app.handlers.activity_collection_handler import ActivityCollectionHandler
        from app.handlers.venue_selection_handler import VenueSelectionHandler
        from app.handlers.final_confirmation_handler import FinalConfirmationHandler
        
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
            )
        }
    
    def route_message(self, phone_number: str, message: str) -> str:
        """Main routing logic - everyone is a planner by default, guest mode per-message only"""
        try:
            # Normalize phone number
            normalized_phone = self._normalize_phone(phone_number)
            
            # Check if they're temporarily responding to an invitation/availability request
            guest_state = GuestState.query.filter_by(phone_number=normalized_phone).first()
            
            if guest_state:
                # Handle as guest (temporary override for responding to invitations)
                response = self._handle_guest_message(guest_state, message)
                
                # IMPORTANT: Always cleanup guest state after each message response
                # Don't wait for workflow completion - return to planner mode immediately
                self._cleanup_guest_state(guest_state)
                
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
            # Check if name is needed
            if not planner.name:
                return self._handle_name_collection(planner, message)
            
            # Handle reset commands
            if message.lower().strip() in ['reset', 'restart', 'start over']:
                return self._handle_reset_command(planner)
            
            # Get active event
            active_event = self._get_active_event(planner.id)
            
            if active_event:
                return self._handle_workflow_message(active_event, message)
            else:
                return self._handle_new_event_request(planner, message)
                
        except Exception as e:
            logger.error(f"Error handling planner message: {e}")
            return self._create_error_response()
    
    def _handle_workflow_message(self, event: Event, message: str) -> str:
        """Route message to appropriate workflow handler"""
        try:
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
            elif current_state == 'awaiting_rsvp':
                return self._handle_rsvp_response(guest_state, message)
            else:
                return self._cleanup_guest_state_and_redirect(guest_state)
                
        except Exception as e:
            logger.error(f"Error handling guest message: {e}")
            return self._create_error_response()
    
    def _handle_availability_response(self, guest_state: GuestState, message: str) -> str:
        """Handle guest availability response - single message, immediate cleanup"""
        try:
            # Parse availability using AI
            context = guest_state.get_state_data()
            parsed_availability = self.ai_service.parse_availability_text(message, context)
            
            if parsed_availability.get('available_dates'):
                # Save availability data
                from app.models.availability import Availability
                from app.models.guest import Guest
                from datetime import datetime
                
                # Find the guest record
                guest = Guest.query.filter_by(
                    event_id=guest_state.event_id,
                    phone_number=guest_state.phone_number
                ).first()
                
                if guest:
                    # Save availability records
                    for avail_data in parsed_availability['available_dates']:
                        availability = Availability(
                            event_id=guest_state.event_id,
                            guest_id=guest.id,
                            date=datetime.strptime(avail_data['date'], '%Y-%m-%d').date(),
                            start_time=datetime.strptime(avail_data['start_time'], '%H:%M').time(),
                            end_time=datetime.strptime(avail_data['end_time'], '%H:%M').time(),
                            all_day=avail_data.get('all_day', False)
                        )
                        availability.save()
                    
                    # Mark guest as having provided availability
                    guest.availability_provided = True
                    guest.save()
                    
                    # Format confirmation response
                    response_text = "Got it! Here's your availability:\n"
                    for avail_data in parsed_availability['available_dates']:
                        date_obj = datetime.strptime(avail_data['date'], '%Y-%m-%d').date()
                        formatted_date = date_obj.strftime('%a, %-m/%-d')
                        start_time = avail_data['start_time']
                        end_time = avail_data['end_time']
                        response_text += f"- {formatted_date}: {start_time} to {end_time}\n"
                    
                    response_text += "\n✅ Thanks! I've recorded your availability. "
                    response_text += f"{guest_state.event.planner.name} will use this to find the best time for everyone."
                    
                    return response_text
            
            return "I couldn't understand your availability. Please try again with something like 'Monday after 2pm' or 'Saturday all day'."
            
        except Exception as e:
            logger.error(f"Error handling availability response: {e}")
            return self._create_error_response("Sorry, there was an error processing your availability.")
    
    def _handle_rsvp_response(self, guest_state: GuestState, message: str) -> str:
        """Handle guest RSVP response - single message, immediate cleanup"""
        try:
            message_lower = message.lower().strip()
            
            # Find the guest record
            from app.models.guest import Guest
            guest = Guest.query.filter_by(
                event_id=guest_state.event_id,
                phone_number=guest_state.phone_number
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
                return response_text
            
            return self._create_error_response("Sorry, there was an error processing your RSVP.")
            
        except Exception as e:
            logger.error(f"Error handling RSVP response: {e}")
            return self._create_error_response("Sorry, there was an error processing your RSVP.")
    
    def _handle_name_collection(self, planner: Planner, message: str) -> str:
        """Handle initial name collection for new planners"""
        name = message.strip()
        if len(name) > 0:
            planner.name = name
            planner.save()
            
            # Create initial event to start workflow
            event = Event(
                planner_id=planner.id,
                workflow_stage='collecting_guests',
                status='planning'
            )
            event.save()
            
            welcome_text = f"Great to meet you, {name}! 👋\n"
            welcome_text += "Let's plan your event!\n\n"
            welcome_text += "Who's coming?\n\n"
            welcome_text += "Reply with guest names and phone numbers (e.g. 'John Doe, 123-456-7890') "
            welcome_text += "or select previous contacts (e.g. '1,2').\n\n"
            welcome_text += "Add one guest at a time.\n\n"
            welcome_text += "💡 Commands:\n"
            welcome_text += "- 'Add guest'\n"
            welcome_text += "- 'Remove contact'\n"
            welcome_text += "- 'Restart'"
            
            return welcome_text
        else:
            return "🎉 Welcome to Event Planner! What's your name?"
    
    def _handle_reset_command(self, planner: Planner) -> str:
        """Handle reset/restart commands"""
        # Cancel any active events
        active_events = Event.query.filter_by(
            planner_id=planner.id,
            status='planning'
        ).all()
        
        for event in active_events:
            event.status = 'cancelled'
            event.save()
        
        return "🔄 Started fresh! What would you like to plan?"
    
    def _handle_new_event_request(self, planner: Planner, message: str) -> str:
        """Handle new event creation requests"""
        # Create new event
        result = self.event_service.create_event_from_text(planner.id, message)
        
        if result['success']:
            event = result['event']
            
            # Check for existing contacts to show
            contacts = Contact.query.filter_by(planner_id=planner.id).order_by(Contact.name).all()
            
            response_text = "Great! Who's coming to your event?\n\n"
            
            if contacts:
                response_text += "Previous contacts:\n"
                for i, contact in enumerate(contacts, 1):
                    response_text += f"{i}. {contact.name}\n"
                response_text += "\nSelect contacts (e.g. '1,3') or add new guests (e.g. 'John Doe, 123-456-7890').\n\n"
            else:
                response_text += "Add guests with names and phone numbers:\n"
                response_text += "Example: 'John Doe, 123-456-7890'\n\n"
            
            response_text += "Reply 'done' when finished adding guests."
            
            return response_text
        else:
            return f"Sorry, I couldn't create your event. {result.get('error', 'Please try again.')}"
    
    def _get_or_create_planner(self, phone_number: str) -> Planner:
        """Get existing planner or create new one"""
        planner = Planner.query.filter_by(phone_number=phone_number).first()
        
        if not planner:
            planner = Planner(phone_number=phone_number)
            planner.save()
        
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
        
        # Route message and get response
        response_text = router.route_message(from_number, message_body)
        
        # Create Twilio response
        resp = MessagingResponse()
        resp.message(response_text)
        
        return str(resp)
        
    except Exception as e:
        logger.error(f"Error in SMS webhook: {e}")
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
