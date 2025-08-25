import logging
from app.handlers import BaseWorkflowHandler, HandlerResult
from app.models.event import Event

logger = logging.getLogger(__name__)

class FinalConfirmationHandler(BaseWorkflowHandler):
    """Handles final event confirmation and invitation sending"""
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            message_lower = message.lower().strip()
            
            # Handle confirmation options
            if message_lower in ['1', 'set a start time', 'set start time', 'start time']:
                # Ask for specific start time
                start_time_prompt = "What time would you like to start?\n\n"
                start_time_prompt += "Examples:\n"
                start_time_prompt += "• '3pm'\n"
                start_time_prompt += "• '7:30pm'\n"
                start_time_prompt += "• '6pm'"
                
                return HandlerResult.success_response(start_time_prompt, 'setting_start_time')
                
            elif message_lower in ['2', 'send', 'send invitations']:
                # Send invitations to all guests
                success_count = 0
                total_guests = len(event.guests)
                
                for guest in event.guests:
                    success = self.guest_service.send_event_invitation(guest)
                    if success:
                        success_count += 1
                
                # Update event status
                event.status = 'finalized'
                event.workflow_stage = 'finalized'
                event.save()
                
                if success_count == total_guests:
                    return HandlerResult.success_response(
                        f"🎉 Event finalized! Invitations sent to all {total_guests} guests.\n\n"
                        "Guests will receive complete event details and can RSVP via SMS."
                    )
                else:
                    return HandlerResult.success_response(
                        f"Event finalized! Sent {success_count}/{total_guests} invitations.\n\n"
                        "Some invitations may have failed. You can check with guests directly."
                    )
            
            elif message_lower in ['3', 'change activity', 'change the activity', 'activity']:
                # Go back to activity selection
                activity_prompt = "🍕 Enter a venue/activity (e.g., Joe's Pizza, Hangout at Jude's)\n\n"
                activity_prompt += "🔮 Or text '1' for activity suggestions"
                
                return HandlerResult.success_response(activity_prompt, 'collecting_activity')
            
            elif message_lower in ['restart', 'start over']:
                # Cancel current event and start fresh
                event.status = 'cancelled'
                event.save()
                
                return HandlerResult.success_response(
                    "🔄 Started fresh! What would you like to plan?",
                    'collecting_guests'
                )
            
            # Handle editing specific parts
            elif message_lower in ['edit date', 'change date', 'dates']:
                date_prompt = "When would you like to have your event?\n\n"
                date_prompt += "Examples:\n"
                date_prompt += "• 'Next Friday and Saturday'\n"
                date_prompt += "• 'December 15-17'"
                
                return HandlerResult.success_response(date_prompt, 'collecting_dates')
            
            elif message_lower in ['edit guests', 'change guests', 'guests']:
                guest_prompt = "Who's coming?\n\n"
                guest_prompt += "Add guests with names and phone numbers:\n"
                guest_prompt += "(E.g., John Doe, 123-456-7890)"
                
                return HandlerResult.success_response(guest_prompt, 'collecting_guests')
            
            elif message_lower in ['edit venue', 'change venue', 'venue']:
                # Go back to venue selection
                if event.venue_suggestions:
                    venue_message = self.message_service.format_venue_suggestions(
                        event.venue_suggestions, event.activity, event.location
                    )
                    return HandlerResult.success_response(venue_message, 'selecting_venue')
                else:
                    return HandlerResult.success_response(
                        "Please enter a venue name:",
                        'selecting_venue'
                    )
            
            elif message_lower in ['edit location', 'change location', 'location']:
                location_prompt = "Where would you like to meet?\n\n"
                location_prompt += "Examples: 'Manhattan', 'Downtown Brooklyn'"
                
                return HandlerResult.success_response(location_prompt, 'collecting_location')
            
            elif message_lower in ['edit activity', 'change activity', 'activity']:
                activity_prompt = "What would you like to do?\n\n"
                activity_prompt += "Examples: 'Coffee', 'Dinner', 'Drinks'"
                
                return HandlerResult.success_response(activity_prompt, 'collecting_activity')
            
            else:
                return HandlerResult.error_response(
                    "Please reply:\n"
                    "1. Set a start time\n"
                    "2. Send invitations to guests\n"
                    "3. Change the activity\n\n"
                    "Or reply 'restart' to start over."
                )
                
        except Exception as e:
            logger.error(f"Error in final confirmation: {e}")
            return HandlerResult.error_response("Sorry, there was an error. Please try again.")
