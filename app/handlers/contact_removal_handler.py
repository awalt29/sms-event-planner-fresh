import logging
from app.handlers import HandlerResult
from app.models.event import Event
from app.models.contact import Contact

logger = logging.getLogger(__name__)

class ContactRemovalHandler:
    """Handler for processing contact removal selection"""
    
    def can_handle(self, event: Event, message: str) -> bool:
        """Check if this handler can process the message"""
        return event.workflow_stage == 'removing_contact'
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        """Handle contact removal selection"""
        try:
            message = message.strip().lower()
            
            # Handle restart command
            if message == 'restart':
                # Parse to get original stage first, before clearing notes
                original_stage = 'collecting_guests'  # default
                if event.notes and event.notes.startswith('removing_contact:'):
                    parts = event.notes.split('removing_contact:')[1].split(':')
                    original_stage = parts[1] if len(parts) > 1 else 'collecting_guests'
                
                event.notes = None
                event.workflow_stage = original_stage
                event.save()
                return self._return_to_original_stage(event, original_stage, "")
            
            # Parse contact data from event notes
            if not event.notes or not event.notes.startswith('removing_contact:'):
                return HandlerResult.error_response(
                    "Contact removal session expired. Please try 'remove contact' again."
                )
            
            parts = event.notes.split('removing_contact:')[1].split(':')
            contact_ids = parts[0].split(',')
            original_stage = parts[1] if len(parts) > 1 else 'collecting_guests'
            
            # Parse selections (support multiple like "1,2,3" or single like "1")
            try:
                if ',' in message:
                    selections = [int(sel.strip()) for sel in message.split(',')]
                else:
                    selections = [int(message)]
            except ValueError:
                return HandlerResult.error_response(
                    "Please reply with the number(s) of the contact(s) you'd like to remove (e.g., '1' or '1,2,3') or say 'restart' to go back."
                )
            
            # Validate all selections
            for selection in selections:
                if selection < 1 or selection > len(contact_ids):
                    return HandlerResult.error_response(
                        f"Please select number(s) between 1 and {len(contact_ids)}."
                    )
            
            # Remove selected contacts
            removed_contacts = []
            for selection in selections:
                contact_id = int(contact_ids[selection - 1])
                contact = Contact.query.filter_by(
                    id=contact_id,
                    planner_id=event.planner.id
                ).first()
                
                if contact:
                    removed_contacts.append({
                        'name': contact.name,
                        'phone': contact.phone_number
                    })
                    contact.delete()
            
            # Clean up and return to original stage
            event.notes = None
            event.workflow_stage = original_stage
            event.save()
            
            # Format success message with bulleted list
            if len(removed_contacts) == 1:
                contact = removed_contacts[0]
                success_message = f"Removed:\n\n- {contact['name']} ({contact['phone']})"
            else:
                success_message = "Removed:\n\n"
                for contact in removed_contacts:
                    success_message += f"- {contact['name']} ({contact['phone']})\n"
                success_message = success_message.rstrip()  # Remove trailing newline
            
            return self._return_to_original_stage(event, original_stage, success_message)
            
        except Exception as e:
            logger.error(f"Error in contact removal handler: {e}")
            return HandlerResult.error_response(
                "Sorry, I couldn't process your request. Please try again."
            )
    
    def _return_to_original_stage(self, event: Event, original_stage: str, prefix_message: str) -> HandlerResult:
        """Return to original stage with appropriate prompt"""
        
        if original_stage == 'collecting_guests':
            # Show contact selection like the original guest collection flow
            contacts = Contact.query.filter_by(planner_id=event.planner.id).all()
            
            if contacts:
                # Build contact selection message
                contact_message = f"{prefix_message}\n\nWho's coming?\n\n"
                contact_message += "Contacts:\n"
                for i, contact in enumerate(contacts, 1):
                    contact_message += f"{i}. {contact.name} ({contact.phone_number})\n"
                
                contact_message += "\nSelect contacts (e.g. '1,3') or add new guests (e.g. 'John Doe, 123-456-7890').\n\n"
                contact_message += "Add one guest at a time.\n\n"
                contact_message += "💡 Commands:\n"
                contact_message += "- 'Remove contact'\n"
                contact_message += "- 'Restart'"
                
                return HandlerResult.success_response(contact_message, original_stage)
            else:
                # No contacts left, show manual input
                manual_message = f"{prefix_message}\n\nWho's coming?\n\n"
                manual_message += "Add guests as: Name, Phone\n"
                manual_message += "(E.g., John Doe, 123-456-7890)\n\n"
                manual_message += "Add one guest at a time.\n\n"
                manual_message += "💡 Commands:\n"
                manual_message += "- 'Remove contact'\n"
                manual_message += "- 'Restart'"
                
                return HandlerResult.success_response(manual_message, original_stage)
        else:
            # For other stages, return with basic prompt
            stage_prompts = {
                'collecting_dates': "When would you like to hang out?\n\nExamples:\n• 'This Friday'\n• 'Next weekend'\n• 'August 15th and 16th'",
                'collecting_availability': "Would you like to:\n1. Pick a time\n2. Add more guests",
                'selecting_time': "Reply with the number of your preferred option (e.g. 1,2,3)",
                'collecting_activity': "What would you like to do and where?\n\nExamples:\n• 'Sushi in Williamsburg'\n• 'Coffee in Tribeca'\n• 'Bowling in Queens'",
                'selecting_venue': "Reply with the number of your preferred venue, or:\n• 'New list' for more options\n• 'Activity' to change activity\n• Enter a venue name manually"
            }
            
            prompt = stage_prompts.get(original_stage, "What would you like to do next?")
            full_message = f"{prefix_message}\n\n{prompt}"
            
            return HandlerResult.success_response(full_message, original_stage)
