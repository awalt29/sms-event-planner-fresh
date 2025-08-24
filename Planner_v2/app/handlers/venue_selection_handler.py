import logging
from app.handlers import BaseWorkflowHandler, HandlerResult
from app.models.event import Event

logger = logging.getLogger(__name__)

class VenueSelectionHandler(BaseWorkflowHandler):
    """Handles venue selection from suggestions or manual input"""
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            message_lower = message.lower().strip()
            
            # Handle venue selection by number
            if message.strip().isdigit():
                venue_number = int(message.strip())
                venues = event.venue_suggestions or []

                if 1 <= venue_number <= 3 and venue_number <= len(venues):
                    selected_venue = venues[venue_number - 1]
                    event.selected_venue = selected_venue
                    event.save()
                    # Generate final confirmation
                    confirmation_msg = self.message_service.format_final_confirmation(event)
                    return HandlerResult.success_response(confirmation_msg, 'final_confirmation')
                elif venue_number == 4:
                    # Generate new list - accumulate all previous venues for exclusion
                    all_previous = event.venue_suggestions or []
                    venues = self.venue_service.get_venue_suggestions(
                        activity=event.activity,
                        location=event.location,
                        exclude_previous=True,
                        previous_venues=all_previous
                    )
                    if venues:
                        # Append new venues to the existing list (don't replace)
                        if event.venue_suggestions:
                            event.venue_suggestions.extend(venues)
                        else:
                            event.venue_suggestions = venues
                        event.save()
                        
                        # Only show the new venues in the response
                        venue_message = self.message_service.format_venue_suggestions(
                            venues, event.activity, event.location
                        )
                        return HandlerResult.success_response(venue_message)
                    else:
                        return HandlerResult.error_response("No more venue suggestions available. Please enter a venue name manually.")
                elif venue_number == 5:
                    # Select a new activity - go back to activity collection
                    activity_prompt = "Let's pick a new activity and location.\n\n"
                    activity_prompt += "Examples:\n"
                    activity_prompt += "• 'Sushi in Williamsburg'\n"
                    activity_prompt += "• 'Coffee in Tribeca'\n"
                    activity_prompt += "• 'Bowling in Queens'"
                    return HandlerResult.success_response(activity_prompt, 'collecting_activity')
                else:
                    return HandlerResult.error_response("Please select 1, 2, 3, 4, or 5.")
            
            # Handle special commands
            elif message_lower == 'new list':
                # Get new venue suggestions - accumulate all previous venues for exclusion
                all_previous = event.venue_suggestions or []
                venues = self.venue_service.get_venue_suggestions(
                    activity=event.activity,
                    location=event.location,
                    exclude_previous=True,
                    previous_venues=all_previous
                )
                if venues:
                    # Append new venues to the existing list (don't replace)
                    if event.venue_suggestions:
                        event.venue_suggestions.extend(venues)
                    else:
                        event.venue_suggestions = venues
                    event.save()
                    
                    # Only show the new venues in the response
                    venue_message = self.message_service.format_venue_suggestions(
                        venues, event.activity, event.location
                    )
                    return HandlerResult.success_response(venue_message)
                else:
                    return HandlerResult.error_response("No more venue suggestions available. Please enter a venue name manually.")
            elif message_lower == 'activity':
                # Go back to activity collection
                activity_prompt = "Let's pick a new activity and location.\n\n"
                activity_prompt += "Examples:\n"
                activity_prompt += "• 'Sushi in Williamsburg'\n"
                activity_prompt += "• 'Coffee in Tribeca'\n"
                activity_prompt += "• 'Bowling in Queens'"
                return HandlerResult.success_response(activity_prompt, 'collecting_activity')
            elif message_lower == 'location':
                # Go back to location collection
                location_prompt = "Where would you like to meet?\n\n"
                location_prompt += "Examples:\n"
                location_prompt += "• 'Manhattan'\n"
                location_prompt += "• 'Downtown Brooklyn'"
                return HandlerResult.success_response(location_prompt, 'collecting_location')
            
            # Handle manual venue input
            else:
                venue_name = message.strip()
                # Validate manual venue input - must be at least 3 characters and not just random text
                if len(venue_name) < 3:
                    return HandlerResult.error_response("Please select 1, 2, 3, 4, or 5, or enter a venue name (at least 3 characters).")
                # Check if it looks like a random/invalid venue name
                if venue_name.lower() in ['hey', 'hi', 'hello', 'test', 'abc', 'xyz', 'aaa', 'bbb']:
                    return HandlerResult.error_response("Please select 1, 2, 3, 4, or 5, or enter a real venue name.")
                # Create manual venue entry
                manual_venue = {
                    'name': venue_name,
                    'type': 'manual',
                    'description': f'Manually entered venue'
                }
                event.selected_venue = manual_venue
                event.save()
                # Generate final confirmation
                confirmation_msg = self.message_service.format_final_confirmation(event)
                return HandlerResult.success_response(confirmation_msg, 'final_confirmation')
        except Exception as e:
            logger.error(f"Error in venue selection: {e}")
            return HandlerResult.error_response("Sorry, there was an error. Please try again.")
