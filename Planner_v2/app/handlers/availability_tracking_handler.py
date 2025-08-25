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
                # Check if we have pending responses (partial overlap mode) or everyone responded (final mode)
                pending_guests = [guest for guest in event.guests if not guest.availability_provided]
                
                if pending_guests:
                    # Partial overlap mode - show current overlaps with subset of guests
                    return self._handle_partial_overlap_request(event)
                else:
                    # Everyone responded - show final overlaps
                    # For single guest case, use show_individual_availability=True
                    responded_guests = [guest for guest in event.guests if guest.availability_provided]
                    show_individual = len(responded_guests) == 1
                    
                    overlaps = self.availability_service.calculate_availability_overlaps(event.id, show_individual_availability=show_individual)
                    if overlaps:
                        time_msg = self.message_service.format_time_selection_options(overlaps, event)
                        return HandlerResult.success_response(time_msg, 'selecting_time')
                    else:
                        time_msg = self.message_service.format_time_selection_options([], event)
                        return HandlerResult.error_response(time_msg)
            
            elif message_lower == '2':
                # Add more guests - use adding_guest stage and preserve current stage
                guest_prompt = "Add more guests:\n\n"
                
                # Show existing contacts for easy selection
                from app.models.contact import Contact
                contacts = Contact.query.filter_by(planner_id=event.planner_id).order_by(Contact.name).all()
                if contacts:
                    guest_prompt += "Contacts:\n"
                    for i, contact in enumerate(contacts, 1):
                        guest_prompt += f"{i}. {contact.name} ({contact.phone_number})\n"
                    guest_prompt += "\nSelect contacts (e.g. '1,3') or add new guests:\n\n"
                
                guest_prompt += "Examples:\n"
                guest_prompt += "- 'John Doe, 111-555-1234'\n"
                guest_prompt += "- 'Mary 5105935336'\n\n"
                guest_prompt += "Reply 'done' when finished adding guests."
                
                # Store current stage to return to after adding guests
                event.previous_workflow_stage = event.workflow_stage
                event.save()
                
                return HandlerResult.success_response(guest_prompt, 'adding_guest')
            
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

    def _handle_partial_overlap_request(self, event: Event) -> HandlerResult:
        """Handle request to view overlaps with partial responses"""
        try:
            # Calculate overlaps with current responses - show individual availability if needed
            overlaps = self.availability_service.calculate_availability_overlaps(event.id, show_individual_availability=True)
            
            if not overlaps:
                return HandlerResult.error_response(
                    "❌ No overlapping times found with current responses. You may need to wait for more guests or add more flexibility."
                )
            
            # Count how many guests have responded
            responded_count = sum(1 for guest in event.guests if guest.availability_provided)
            total_count = len(event.guests)
            pending_guests = [guest for guest in event.guests if not guest.availability_provided]
            
            # Format partial overlap message
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
                overlap_msg += f"Attendance: {len(guest_names)}/{responded_count} responded\n"
                overlap_msg += f"Available: {', '.join(guest_names)}\n\n"
            
            overlap_msg += f"Still waiting for: {', '.join([g.name for g in pending_guests])}\n\n"
            overlap_msg += "Reply with the number of your preferred option (e.g., 1, 2, 3) or wait for the remaining guests to respond."
            
            # Change to partial selection mode
            return HandlerResult.success_response(overlap_msg, 'selecting_partial_time')
            
        except Exception as e:
            logger.error(f"Error in partial overlap request: {e}")
            return HandlerResult.error_response("Sorry, there was an error calculating overlaps.")
