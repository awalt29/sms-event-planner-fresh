import logging
from app.handlers import BaseWorkflowHandler, HandlerResult
from app.models.event import Event

logger = logging.getLogger(__name__)

class LocationCollectionHandler(BaseWorkflowHandler):
    """Handles location collection for venue searching"""
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            location = message.strip()
            
            if len(location) > 0:
                # Store location in event
                event.location = location
                event.save()
                
                # Transition to activity collection
                activity_prompt = "Great! Now what would you like to do?\n\n"
                activity_prompt += "Examples:\n"
                activity_prompt += "• 'Coffee'\n"
                activity_prompt += "• 'Chinese food'\n"
                activity_prompt += "• 'Boozy Brunch'\n"
                activity_prompt += "• 'Drinks at a rooftop bar'"
                
                return HandlerResult.success_response(activity_prompt, 'collecting_activity')
            else:
                return HandlerResult.error_response("Please enter a location.")
                
        except Exception as e:
            logger.error(f"Error in location collection: {e}")
            return HandlerResult.error_response("Sorry, there was an error. Please try again.")
