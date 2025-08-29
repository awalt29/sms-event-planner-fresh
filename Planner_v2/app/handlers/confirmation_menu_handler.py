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
                    "💌 Availability requests sent via SMS!\n\nSend 'Add Guests' to add more guests or 'Status' to see who haasn't responded.",
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
                # Add more guests - preserve current stage and transition to adding_guest
                guest_prompt = "Add more guests:\n\n"
                
                # Show existing contacts for easy selection
                from app.models.contact import Contact
                contacts = Contact.query.filter_by(planner_id=event.planner_id).order_by(Contact.name).all()
                if contacts:
                    guest_prompt += "Contacts:\n"
                    for i, contact in enumerate(contacts, 1):
                        guest_prompt += f"{i}. {contact.name} ({contact.phone_number})\n"
                    guest_prompt += "\nSelect contacts (e.g. '1,3') or add new guests:\n\n"
                
                guest_prompt += "Examples:\n"
                guest_prompt += "- 'John Doe, 111-555-1234'\n"
                guest_prompt += "- 'Mary 5105935336'\n\n"
                guest_prompt += "Reply 'done' when finished adding guests."
                
                # Store current stage to return to after adding guests
                event.previous_workflow_stage = event.workflow_stage
                event.save()
                
                return HandlerResult.success_response(guest_prompt, 'adding_guest')
                
            else:
                return HandlerResult.error_response("Please reply with 1, 2, or 3 to choose an option.")
                
        except Exception as e:
            logger.error(f"Error in confirmation menu: {e}")
            return HandlerResult.error_response("Sorry, there was an error. Please try again.")
