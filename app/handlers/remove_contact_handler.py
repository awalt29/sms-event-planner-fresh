import logging
from app.handlers import HandlerResult
from app.models.event import Event
from app.models.contact import Contact

logger = logging.getLogger(__name__)

class RemoveContactHandler:
    """Global handler for removing contacts from planner's contact list"""
    
    def can_handle(self, event: Event, message: str) -> bool:
        """Check if this handler can process the message"""
        return message.lower().strip() in ['remove contact', 'remove contacts']
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        """Handle contact removal request"""
        try:
            # Get planner's contacts
            contacts = Contact.query.filter_by(planner_id=event.planner.id).all()
            
            if not contacts:
                return HandlerResult.success_response(
                    "You don't have any contacts to remove.",
                    event.workflow_stage
                )
            
            # Build contact list with numbers
            contact_list = "Which contacts would you like to remove?\n\n"
            for i, contact in enumerate(contacts, 1):
                contact_list += f"{i}. {contact.name} ({contact.phone_number})\n"
            
            contact_list += "\nReply with the number of your choice (e.g., 1,2) or say 'restart' to go back"
            
            # Store contact IDs and previous stage for removal process
            contact_ids = [str(contact.id) for contact in contacts]
            event.notes = f"removing_contact:{','.join(contact_ids)}:{event.workflow_stage}"
            event.save()
            
            return HandlerResult.success_response(contact_list, 'removing_contact')
            
        except Exception as e:
            logger.error(f"Error in remove contact handler: {e}")
            return HandlerResult.error_response(
                "Sorry, I couldn't process your request. Please try again."
            )
