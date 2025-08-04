import logging
from app.handlers import BaseWorkflowHandler, HandlerResult
from app.models.event import Event

logger = logging.getLogger(__name__)

class ActivityCollectionHandler(BaseWorkflowHandler):
    """Handles activity collection for venue searching"""
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            activity = message.strip()
            
            if len(activity) > 0:
                # Store activity in event
                event.activity = activity
                event.save()
                
                # Get venue suggestions
                venues = self.venue_service.get_venue_suggestions(
                    activity=activity,
                    location=event.location
                )
                
                if venues and len(venues) > 0:
                    # Store suggestions in event
                    event.venue_suggestions = venues
                    event.save()
                    
                    # Format venue suggestions message
                    venue_message = self.message_service.format_venue_suggestions(
                        venues, activity, event.location
                    )
                    
                    return HandlerResult.success_response(venue_message, 'selecting_venue')
                else:
                    # No venues found, ask for manual input
                    fallback_msg = f"I couldn't find specific venues for {activity} in {event.location}.\n\n"
                    fallback_msg += "Please enter a venue name or description:"
                    
                    return HandlerResult.success_response(fallback_msg, 'selecting_venue')
            else:
                return HandlerResult.error_response("Please enter an activity.")
                
        except Exception as e:
            logger.error(f"Error in activity collection: {e}")
            return HandlerResult.error_response("Sorry, there was an error. Please try again.")
