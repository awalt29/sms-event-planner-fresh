import logging
from datetime import time
from app.handlers import BaseWorkflowHandler, HandlerResult
from app.models.event import Event

logger = logging.getLogger(__name__)

class StartTimeSettingHandler(BaseWorkflowHandler):
    """Handles setting a specific start time for events"""
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            message_text = message.strip()
            
            # Parse the start time using AI service
            parsed_time = self.ai_service.parse_time_input(message_text)
            
            if parsed_time.get('success'):
                # Extract the time components
                start_hour = parsed_time.get('start_hour')
                start_minute = parsed_time.get('start_minute', 0)
                
                if start_hour is not None:
                    # Create time object
                    new_start_time = time(start_hour, start_minute)
                    
                    # Validate the time is within the available window
                    if self._is_time_within_window(event, new_start_time):
                        # Update the event with the new start time
                        event.selected_start_time = new_start_time
                        
                        # Mark in notes that user set this start time
                        current_notes = event.notes or ""
                        if "USER_SET_START_TIME" not in current_notes:
                            event.notes = f"{current_notes}\nUSER_SET_START_TIME=True"
                        
                        # Set a default 2-hour duration if we don't have an end time
                        if not event.selected_end_time or event.selected_end_time <= new_start_time:
                            end_hour = (start_hour + 2) % 24
                            event.selected_end_time = time(end_hour, start_minute)
                        
                        event.save()
                        
                        # Return to final confirmation with updated time
                        confirmation_msg = self.message_service.format_final_confirmation(event)
                        return HandlerResult.success_response(confirmation_msg, 'final_confirmation')
                    else:
                        return HandlerResult.error_response(
                            f"The time {message_text} is not within your available window. "
                            "Please choose a time when everyone is available."
                        )
                else:
                    return HandlerResult.error_response(
                        "I couldn't understand that time. Please try again with formats like '3pm', '7:30pm', or '6pm'."
                    )
            else:
                return HandlerResult.error_response(
                    "Please enter a valid start time (e.g., '3pm', '7:30pm', '6pm')."
                )
                
        except Exception as e:
            logger.error(f"Error in start time setting: {e}")
            return HandlerResult.error_response("Sorry, there was an error. Please try again.")
    
    def _is_time_within_window(self, event: Event, proposed_time: time) -> bool:
        """Check if the proposed time is within the event's available window"""
        try:
            # If we have selected start/end times, check against those
            if event.selected_start_time and event.selected_end_time:
                original_start = event.selected_start_time
                original_end = event.selected_end_time
                
                # Handle cases where end time is before start time (crosses midnight)
                if original_end < original_start:
                    # Event crosses midnight
                    return proposed_time >= original_start or proposed_time <= original_end
                else:
                    # Normal case
                    return original_start <= proposed_time <= original_end
            
            # If no specific window, allow any reasonable time (6am-midnight)
            return time(6, 0) <= proposed_time <= time(23, 59)
            
        except Exception as e:
            logger.error(f"Error checking time window: {e}")
            # Be permissive on error
            return True
