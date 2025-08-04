import logging
from app.handlers import BaseWorkflowHandler, HandlerResult
from app.models.event import Event

logger = logging.getLogger(__name__)

class TimeSelectionHandler(BaseWorkflowHandler):
    """Handles time selection after availability collection"""
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            # For now, store the selected time and move to location collection
            # In a full implementation, this would analyze availability overlaps
            # and present optimal time slots
            
            message_lower = message.lower().strip()
            
            # Handle time selection (e.g., "1", "2", "3" for time slot options)
            if message.strip().isdigit():
                slot_number = int(message.strip())
                
                # Mock time selection - in real implementation would use availability data
                if slot_number == 1:
                    time_text = "2:00pm-6:00pm"
                elif slot_number == 2:
                    time_text = "6:00pm-10:00pm"
                else:
                    time_text = "Evening"
                
                # Store selected time in notes
                current_notes = event.notes or ""
                event.notes = f"{current_notes}\nSelected time: {time_text}"
                event.save()
                
                # Transition to location collection
                location_prompt = "Perfect! Now where would you like to meet?\n\n"
                location_prompt += "Examples:\n"
                location_prompt += "• 'Manhattan'\n"
                location_prompt += "• 'Downtown Brooklyn'\n"
                location_prompt += "• 'Central Park area'"
                
                return HandlerResult.success_response(location_prompt, 'collecting_location')
            
            # Handle natural language time input
            else:
                # Use AI to parse time preferences
                parsed_time = self.ai_service.parse_time_selection(message)
                
                if parsed_time.get('success'):
                    time_text = parsed_time.get('time_text', message)
                    
                    # Store selected time
                    current_notes = event.notes or ""
                    event.notes = f"{current_notes}\nSelected time: {time_text}"
                    event.save()
                    
                    # Transition to location collection
                    location_prompt = "Perfect! Now where would you like to meet?\n\n"
                    location_prompt += "Examples:\n"
                    location_prompt += "• 'Manhattan'\n"
                    location_prompt += "• 'Downtown Brooklyn'\n"
                    location_prompt += "• 'Central Park area'"
                    
                    return HandlerResult.success_response(location_prompt, 'collecting_location')
                else:
                    return HandlerResult.error_response(
                        "I couldn't understand that time. Please try again or pick a number from the options above."
                    )
                
        except Exception as e:
            logger.error(f"Error in time selection: {e}")
            return HandlerResult.error_response("Sorry, there was an error selecting the time.")
