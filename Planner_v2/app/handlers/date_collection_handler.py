import logging
from app.handlers import BaseWorkflowHandler, HandlerResult
from app.models.event import Event

logger = logging.getLogger(__name__)

class DateCollectionHandler(BaseWorkflowHandler):
    """Handles date collection workflow stage"""
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            # Parse dates using AI
            parsed_dates = self.ai_service.parse_natural_language_dates(message)
            
            if parsed_dates.get('success'):
                # Save dates to event
                event.notes = f"Proposed dates: {parsed_dates['dates_text']}"
                event.save()
                
                # Generate confirmation menu
                confirmation_msg = self.message_service.format_planner_confirmation_menu(event)
                return HandlerResult.success_response(confirmation_msg, 'awaiting_confirmation')
            else:
                return HandlerResult.error_response(
                    "I couldn't understand those dates. Please try again with a clearer format like '8/1-8/4' or 'Saturday and Sunday'."
                )
                
        except Exception as e:
            logger.error(f"Error in date collection: {e}")
            return HandlerResult.error_response("Sorry, there was an error processing the dates.")
