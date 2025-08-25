import logging
from datetime import time
from app.handlers import BaseWorkflowHandler, HandlerResult
from app.models.event import Event
from app.services.availability_service import AvailabilityService

logger = logging.getLogger(__name__)

class TimeSelectionHandler(BaseWorkflowHandler):
    """Handles time selection after availability collection"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.availability_service = AvailabilityService()
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            message_lower = message.lower().strip()
            
            # Handle time selection (e.g., "1", "2", "3" for time slot options)
            if message.strip().isdigit():
                slot_number = int(message.strip())
                
                # Get the actual availability overlaps for this event
                # Use same logic as availability tracking handler for consistency
                responded_guests = [guest for guest in event.guests if guest.availability_provided]
                show_individual = len(responded_guests) == 1
                overlaps = self.availability_service.calculate_availability_overlaps(event.id, show_individual_availability=show_individual)
                
                if overlaps and 1 <= slot_number <= len(overlaps):
                    selected_overlap = overlaps[slot_number - 1]
                    
                    # Format the time text using actual overlap data
                    if selected_overlap.get('all_day'):
                        time_text = f"{selected_overlap['date'].strftime('%A, %B %-d')} - All day"
                    else:
                        start_time = selected_overlap.get('start_time', '00:00')
                        end_time = selected_overlap.get('end_time', '23:59')
                        date_str = selected_overlap['date'].strftime('%A, %B %-d')
                        time_text = f"{date_str}: {start_time}-{end_time}"
                    
                    # Convert string times to time objects for database storage
                    def parse_time_string(time_str):
                        """Convert time string like '14:00' to time object"""
                        if isinstance(time_str, str) and ':' in time_str:
                            hour, minute = map(int, time_str.split(':'))
                            return time(hour, minute)
                        elif hasattr(time_str, 'time'):  # It's already a time object
                            return time_str
                        else:
                            return None
                    
                    # Store selected time in event
                    event.selected_date = selected_overlap['date']
                    event.selected_start_time = parse_time_string(selected_overlap.get('start_time'))
                    event.selected_end_time = parse_time_string(selected_overlap.get('end_time'))
                    
                    # Store available guests for this selected time
                    available_guests = selected_overlap.get('available_guests', [])
                    import json
                    current_notes = event.notes or ""
                    event.notes = f"{current_notes}\nSelected available guests: {json.dumps(available_guests)}"
                    event.save()
                    
                    # Transition to activity collection with venue options
                    activity_prompt = "Perfect! Time selected. Now for the activity:\n\n"
                    activity_prompt += "🍕 Enter a venue/activity (e.g., Joe's Pizza, Hangout at Jude's)\n\n"
                    activity_prompt += "🔮 Or text '1' for activity suggestions\n\n"
                    
                    return HandlerResult.success_response(activity_prompt, 'collecting_activity')
                else:
                    return HandlerResult.error_response(f"Please select a number between 1 and {len(overlaps) if overlaps else 0}.")
            
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
                    
                    # Transition to combined activity/location collection with venue options
                    activity_prompt = "Perfect! Now for the venue:\n\n"
                    activity_prompt += "🍕 Enter a specific place (e.g., 'Shake Shack', 'Joe's Pizza')\n"
                    activity_prompt += "🎯 Or text '1' for activity suggestions\n\n"
                    activity_prompt += "Examples of specific places:\n"
                    activity_prompt += "• Shake Shack\n"
                    activity_prompt += "• Starbucks\n"
                    activity_prompt += "• Central Park"
                    return HandlerResult.success_response(activity_prompt, 'collecting_activity')
                else:
                    return HandlerResult.error_response(
                        "I couldn't understand that time. Please try again or pick a number from the options above."
                    )
                
        except Exception as e:
            logger.error(f"Error in time selection: {e}")
            return HandlerResult.error_response("Sorry, there was an error selecting the time.")
