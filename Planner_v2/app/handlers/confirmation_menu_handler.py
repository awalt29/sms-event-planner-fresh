import logging
from app.handlers import BaseWorkflowHandler, HandlerResult
from app.models.event import Event

logger = logging.getLogger(__name__)

class ConfirmationMenuHandler(BaseWorkflowHandler):
    """Handles the 3-option confirmation menu"""
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            choice = message.strip()
            
            if choice == '1':
                # Send availability requests
                for guest in event.guests:
                    self.guest_service.send_availability_request(guest)
                
                return HandlerResult.success_response(
                    "Availability requests sent via SMS!",
                    'collecting_availability'
                )
                
            elif choice == '2':
                # Change dates
                response_text = "What dates are you thinking for your event?\n\n"
                response_text += "You can say things like:\n"
                response_text += "- 'Saturday and Sunday'\n"
                response_text += "- '7/12,7/13,7/14'\n"
                response_text += "- '8/5-8/12'\n"
                response_text += "- 'friday to monday'"
                
                return HandlerResult.success_response(response_text, 'collecting_dates')
                
            elif choice == '3':
                # Add more guests
                return HandlerResult.transition_to('collecting_guests')
                
            else:
                return HandlerResult.error_response("Please reply with 1, 2, or 3 to choose an option.")
                
        except Exception as e:
            logger.error(f"Error in confirmation menu: {e}")
            return HandlerResult.error_response("Sorry, there was an error. Please try again.")
