import logging
from datetime import time
from app.handlers import BaseWorkflowHandler, HandlerResult
from app.models.event import Event
from app.services.availability_service import AvailabilityService

logger = logging.getLogger(__name__)

class PartialTimeSelectionHandler(BaseWorkflowHandler):
    """Handles time selection from partial availability responses"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.availability_service = AvailabilityService()
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            message_lower = message.lower().strip()
            
            # Handle time selection (e.g., "1", "2", "3" for time slot options)
            if message.strip().isdigit():
                slot_number = int(message.strip())
                
                # Get the actual availability overlaps for this event (with partial responses)
                overlaps = self.availability_service.calculate_availability_overlaps(event.id, show_individual_availability=True)
                
                # Special case: "2" could mean "continue waiting" if there's only one overlap
                if slot_number == 2 and len(overlaps) == 1:
                    # Return to availability tracking mode
                    status_msg = self.message_service.format_availability_status(event)
                    return HandlerResult.success_response(status_msg, 'tracking_availability')
                
                # Handle actual time slot selection
                if overlaps and 1 <= slot_number <= len(overlaps):
                    selected_overlap = overlaps[slot_number - 1]
                    
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
                    
                    # Transition directly to activity collection (like normal flow)
                    activity_prompt = "🍕 Enter a venue/activity (e.g., Joe's Pizza, Hangout at Jude's)\n\n"
                    activity_prompt += "🔮 Or text '1' for activity suggestions"
                    
                    return HandlerResult.success_response(activity_prompt, 'collecting_activity')
                else:
                    # Invalid slot number - provide helpful error message
                    if len(overlaps) == 1:
                        return HandlerResult.error_response("Please reply with '1' to select the time slot or '2' to continue waiting.")
                    else:
                        return HandlerResult.error_response(f"Please select a number between 1 and {len(overlaps)}, or reply '2' to continue waiting.")
            
            # Handle option 2 - continue waiting
            elif message_lower == '2':
                # Return to availability tracking mode
                status_msg = self.message_service.format_availability_status(event)
                return HandlerResult.success_response(status_msg, 'tracking_availability')
            
            else:
                # Invalid input - show partial overlaps again
                return self._show_partial_overlaps_again(event)
                
        except Exception as e:
            logger.error(f"Error in partial time selection: {e}")
            return HandlerResult.error_response("Sorry, there was an error selecting the time.")
    
    def _show_partial_overlaps_again(self, event: Event) -> HandlerResult:
        """Re-show partial overlaps if invalid input"""
        try:
            overlaps = self.availability_service.calculate_availability_overlaps(event.id, show_individual_availability=True)
            
            if not overlaps:
                return HandlerResult.error_response(
                    "❌ No overlapping times found. Returning to availability tracking."
                )
            
            # Count responses
            responded_count = sum(1 for guest in event.guests if guest.availability_provided)
            total_count = len(event.guests)
            pending_guests = [guest for guest in event.guests if not guest.availability_provided]
            
            # Format message
            overlap_msg = f"⏰ Current Overlaps (based on {responded_count}/{total_count} responses):\n\n"
            
            for i, overlap in enumerate(overlaps, 1):
                date_str = overlap['date'].strftime('%a, %-m/%-d') if overlap['date'] else 'TBD'
                
                # Format times to 12-hour format
                start_time = overlap['start_time']
                end_time = overlap['end_time']
                
                # Convert to readable format (like in format_time_selection_options)
                if start_time == '08:00' and end_time == '23:59':
                    time_range = "All day"
                else:
                    start_12hr = self.message_service._format_time_12hr(start_time)
                    end_12hr = self.message_service._format_time_12hr(end_time)
                    time_range = f"{start_12hr}-{end_12hr}"
                
                guest_names = overlap.get('available_guests', [])
                
                overlap_msg += f"{i}. {date_str}: {time_range}\n"
                overlap_msg += f"Available: {', '.join(guest_names)}\n\n"
            
            overlap_msg += f"Still waiting for: {', '.join([g.name for g in pending_guests])}\n\n"
            overlap_msg += "Reply with the number of your preferred option (e.g., 1, 2, 3) or wait for the remaining guests to respond."
            
            return HandlerResult.success_response(overlap_msg)
            
        except Exception as e:
            logger.error(f"Error showing partial overlaps: {e}")
            return HandlerResult.error_response("Sorry, there was an error. Returning to availability tracking.")
