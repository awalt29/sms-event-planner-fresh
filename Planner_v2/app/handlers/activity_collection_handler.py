import logging
from app.handlers import BaseWorkflowHandler, HandlerResult
from app.models.event import Event

logger = logging.getLogger(__name__)

class ActivityCollectionHandler(BaseWorkflowHandler):
    """Handles activity collection for venue searching"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from app.services.ai_processing_service import AIProcessingService
        self.ai_service = AIProcessingService()

    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            message_text = message.strip()
            
            # Handle "1" for activity suggestions
            if message_text == "1":
                activity_prompt = "What would you like to do and where?\n\n"
                activity_prompt += "Examples:\n"
                activity_prompt += "• 'Sushi in Williamsburg'\n"
                activity_prompt += "• 'Coffee in Tribeca'\n"
                activity_prompt += "• 'Bowling in Queens'\n"
                return HandlerResult.success_response(activity_prompt, 'collecting_activity')
            
            # Check if this looks like an activity+location format (contains "in", "at", etc.)
            if self._is_activity_location_format(message_text):
                # Parse as activity + location and get venue suggestions
                return self._handle_activity_location(event, message_text)
            
            # Otherwise treat as direct venue name
            venue_name = message_text
            event.activity = venue_name
            event.location = "your area"
            event.save()
            
            # Generate final confirmation
            confirmation_msg = self.message_service.format_final_confirmation(event)
            return HandlerResult.success_response(confirmation_msg, 'final_confirmation')
                    
        except Exception as e:
            logger.error(f"Error in activity collection: {e}")
            return HandlerResult.error_response("Sorry, there was an error processing your request.")

    def _ai_parse_activity_location(self, message: str) -> dict:
        import json
        try:
            prompt = f'''Parse this message into an activity and location for event planning.
Message: "{message}"

Extract:
1. Activity: What they want to do (e.g., "coffee", "dinner", "Chinese food", "drinks")
2. Location: Where they want to do it (e.g., "Brooklyn", "Manhattan", "downtown")

Examples:
- "Chinese food in Brooklyn" → {{"activity": "Chinese food", "location": "Brooklyn"}}
- "coffee in Manhattan" → {{"activity": "coffee", "location": "Manhattan"}}
- "dinner at downtown" → {{"activity": "dinner", "location": "downtown"}}

If the activity or location is unclear, return null for that field.
Return JSON only: {{"activity": "...", "location": "..."}}'''

            logger.info(f"[AI DEBUG] Processing message: '{message}'")
            response = self.ai_service.make_completion(prompt, max_tokens=150)
            logger.info(f"[AI DEBUG] Raw AI response: '{response}'")
            
            if response:
                parsed = json.loads(response)
                logger.info(f"[AI DEBUG] Parsed JSON successfully: {parsed}")
                
                # Validate AI response - reject if contains "Unknown" or empty values
                activity = parsed.get('activity', '').strip()
                location = parsed.get('location', '').strip()
                
                logger.info(f"[AI DEBUG] Extracted - activity: '{activity}', location: '{location}'")
                
                if (activity and location and 
                    activity.lower() not in ['unknown', 'unclear', ''] and 
                    location.lower() not in ['unknown', 'unclear', '']):
                    logger.info(f"[AI DEBUG] AI parsing successful for '{message}'")
                    return {'activity': activity, 'location': location}
                else:
                    logger.warning(f"[AI DEBUG] AI returned invalid values - activity: '{activity}', location: '{location}'")
            else:
                logger.warning(f"[AI DEBUG] AI service returned empty response for '{message}'")
            
            # If AI fails or returns invalid data, fall back to regex
            logger.info(f"[AI DEBUG] Falling back to regex parsing for '{message}'")
            return self._fallback_parse(message)
            
        except json.JSONDecodeError as e:
            logger.error(f"[AI DEBUG] JSON decode error for '{message}': {e}")
            logger.error(f"[AI DEBUG] Invalid JSON response: '{response}'")
            # Fallback to regex parsing
            return self._fallback_parse(message)
        except Exception as e:
            logger.error(f"[AI DEBUG] General parsing error for '{message}': {e}")
            # Fallback to regex parsing
            return self._fallback_parse(message)
    
    def _fallback_parse(self, message: str) -> dict:
        """Fallback regex parsing for activity and location"""
        logger.info(f"[FALLBACK DEBUG] Starting fallback parsing for: '{message}'")
        
        msg_lower = message.lower().strip()
        
        # Try ' in ' pattern first
        if ' in ' in msg_lower:
            parts = message.split(' in ', 1)
            activity = parts[0].strip()
            location = parts[1].strip()
            if activity and location:
                logger.info(f"[FALLBACK DEBUG] Successfully parsed with 'in' pattern - activity: '{activity}', location: '{location}'")
                return {'activity': activity, 'location': location}
        
        # Try ' at ' pattern
        elif ' at ' in msg_lower:
            parts = message.split(' at ', 1)
            activity = parts[0].strip()
            location = parts[1].strip()
            if activity and location:
                logger.info(f"[FALLBACK DEBUG] Successfully parsed with 'at' pattern - activity: '{activity}', location: '{location}'")
                return {'activity': activity, 'location': location}
        
        # If no clear pattern, treat whole message as activity
        logger.warning(f"[FALLBACK DEBUG] No clear pattern found, using whole message as activity: '{message.strip()}'")
        return {'activity': message.strip(), 'location': 'your area'}

    def _is_activity_location_format(self, message: str) -> bool:
        """Check if message contains activity + location pattern"""
        message_lower = message.lower()
        
        # First check for venue-like patterns that should NOT be treated as activity+location
        # These are specific venue names that contain location words
        venue_indicators = [
            "'s",  # Possessive names like "Joe's", "Jude's"  
            " house", " home", " place", " apartment", " apt",
        ]
        
        # If it contains possessive or venue indicators, treat as single venue name
        if any(indicator in message_lower for indicator in venue_indicators):
            return False
            
        # Now check for genuine activity + location patterns
        location_patterns = [' in ', ' near ', ' around ']
        
        # For "at", be more careful - only count as activity+location if it follows typical patterns
        if ' at ' in message_lower:
            # "at" patterns that suggest activity + location:
            # "dinner at downtown", "coffee at the mall", "drinks at times square"
            # NOT: "Hangout at Jude's", "Party at Mike's"
            at_parts = message_lower.split(' at ')
            if len(at_parts) == 2:
                activity_part = at_parts[0].strip()
                location_part = at_parts[1].strip()
                
                # If the location part looks like a proper noun (title case) or possessive,
                # it's likely a venue name, not a location
                if ("'" in location_part or 
                    location_part.replace("'s", "").replace(" ", "").isalpha()):
                    return False
                    
                # If activity part is very generic, it's probably a venue name
                generic_activities = ['hangout', 'party', 'gathering', 'event', 'meeting']
                if activity_part in generic_activities:
                    return False
        
        return any(pattern in message_lower for pattern in location_patterns)

    def _handle_activity_location(self, event: Event, message: str) -> HandlerResult:
        """Handle activity + location input and get venue suggestions"""
        try:
            # Parse activity and location
            message_lower = message.lower()
            for pattern in [' in ', ' at ', ' near ', ' around ']:
                if pattern in message_lower:
                    parts = message.split(pattern, 1)
                    if len(parts) == 2:
                        activity = parts[0].strip()
                        location = parts[1].strip()
                        
                        # Store activity and location
                        event.activity = activity
                        event.location = location
                        event.save()
                        
                        # Get venue suggestions
                        venues = self.venue_service.get_venue_suggestions(activity, location)
                        
                        if venues:
                            event.venue_suggestions = venues
                            event.save()
                            venue_message = self.message_service.format_venue_suggestions(
                                venues, activity, location
                            )
                            return HandlerResult.success_response(venue_message, 'selecting_venue')
                        else:
                            return HandlerResult.error_response(
                                "No venues found for that activity and location. Please try a different combination."
                            )
            
            # If we get here, parsing failed
            return HandlerResult.error_response(
                "Please specify what you'd like to do and where (e.g. 'Sushi in Williamsburg')"
            )
            
        except Exception as e:
            logger.error(f"Error handling activity location: {e}")
            return HandlerResult.error_response(
                "Sorry, I couldn't process that. Please try again."
            )
