import logging
from app.handlers import BaseWorkflowHandler, HandlerResult
from app.models.event import Event
from app.services.availability_service import AvailabilityService

logger = logging.getLogger(__name__)

class AvailabilityTrackingHandler(BaseWorkflowHandler):
    """Handles availability tracking and status updates"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.availability_service = AvailabilityService()
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            message_lower = message.lower().strip()
            
            if message_lower == 'status':
                # Show availability status
                status_msg = self.message_service.format_availability_status(event)
                return HandlerResult.success_response(status_msg)
            
            elif message_lower == 'remind':
                # Send reminder messages
                return self._send_reminder_messages(event)
            
            elif message_lower == '1':
                # Pick a time - calculate overlaps
                overlaps = self.availability_service.calculate_availability_overlaps(event.id)
                if overlaps:
                    time_msg = self.message_service.format_time_selection_options(overlaps)
                    return HandlerResult.success_response(time_msg, 'selecting_time')
                else:
                    return HandlerResult.error_response(
                        "❌ No overlapping times found. You may need to add more flexibility or different dates."
                    )
            
            elif message_lower == '2':
                # Add more guests
                return HandlerResult.transition_to('collecting_guests')
            
            else:
                # Default response
                status_msg = self.message_service.format_availability_status(event)
                return HandlerResult.success_response(status_msg)
                
        except Exception as e:
            logger.error(f"Error in availability tracking: {e}")
            return HandlerResult.error_response("Sorry, there was an error. Please try again.")
    
    def _send_reminder_messages(self, event: Event) -> HandlerResult:
        """Send reminder messages to pending guests"""
        try:
            pending_guests = [guest for guest in event.guests if not guest.availability_provided]
            
            if not pending_guests:
                return HandlerResult.error_response("All guests have already responded!")
            
            sent_count = 0
            for guest in pending_guests:
                if self.guest_service.send_availability_request(guest):
                    sent_count += 1
            
            if sent_count > 0:
                return HandlerResult.success_response(
                    f"Reminder messages sent to {sent_count} guest{'s' if sent_count != 1 else ''}!"
                )
            else:
                return HandlerResult.error_response("Failed to send reminder messages.")
                
        except Exception as e:
            logger.error(f"Error sending reminders: {e}")
            return HandlerResult.error_response("Sorry, there was an error sending reminders.")
