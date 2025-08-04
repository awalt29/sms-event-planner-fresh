import logging
import json
import re
from datetime import datetime, timedelta
from app.handlers import BaseWorkflowHandler, HandlerResult
from app.models.event import Event
from app.services.ai_processing_service import AIProcessingService

logger = logging.getLogger(__name__)

class DateCollectionHandler(BaseWorkflowHandler):
    """Handles date collection workflow stage"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ai_service = AIProcessingService()
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            # Parse dates using AI for this step
            date_data = self._parse_date_input(message)
            
            if date_data['success']:
                # Save dates to event
                event.notes = f"Proposed dates: {date_data['dates_text']}"
                event.save()
                
                # Generate confirmation menu
                confirmation_msg = self.message_service.format_planner_confirmation_menu(event)
                return HandlerResult.success_response(confirmation_msg, 'awaiting_confirmation')
            else:
                return HandlerResult.error_response(
                    "I couldn't understand those dates. Please try again with a clearer format like:\n"
                    "- 'Saturday and Sunday'\n"
                    "- 'Next Friday'\n"
                    "- 'December 15-17'"
                )
                
        except Exception as e:
            logger.error(f"Error in date collection: {e}")
            return HandlerResult.error_response("Sorry, there was an error processing the dates.")

    def _parse_date_input(self, text: str) -> dict:
        """Parse date input specific to date collection step"""
        # Try AI parsing first
        ai_result = self._ai_parse_dates(text)
        if ai_result:
            return ai_result
        
        # Fallback to simple parsing for this step
        return self._simple_parse_dates(text)
    
    def _ai_parse_dates(self, text: str) -> dict:
        """AI parsing for date collection step only"""
        try:
            today = datetime.now().strftime('%A, %B %d, %Y')
            
            prompt = f"""Parse dates from: "{text}"
Today is {today}

Return JSON with:
- success: true/false
- dates: array of YYYY-MM-DD strings
- dates_text: human readable summary

Examples:
"Monday" -> {{"success": true, "dates": ["2025-08-05"], "dates_text": "Monday, August 5"}}
"Saturday and Sunday" -> {{"success": true, "dates": ["2025-08-09", "2025-08-10"], "dates_text": "Saturday and Sunday"}}
"next week" -> {{"success": false, "error": "Please be more specific"}}"""

            response = self.ai_service.make_completion(prompt, 250)
            if response:
                result = json.loads(response)
                logger.info(f"Date collection AI parsing successful: {result}")
                return result
                
        except Exception as e:
            logger.error(f"Date collection AI parsing error: {e}")
            
        return None
    
    def _simple_parse_dates(self, text: str) -> dict:
        """Simple fallback for date collection step"""
        text_lower = text.lower().strip()
        today = datetime.now()
        
        if 'monday' in text_lower:
            next_monday = today + timedelta(days=(7 - today.weekday()))
            return {
                'success': True,
                'dates': [next_monday.strftime('%Y-%m-%d')],
                'dates_text': f"Monday, {next_monday.strftime('%B %d')}"
            }
        elif 'tuesday' in text_lower:
            next_tuesday = today + timedelta(days=((1 - today.weekday()) % 7))
            return {
                'success': True,
                'dates': [next_tuesday.strftime('%Y-%m-%d')],
                'dates_text': f"Tuesday, {next_tuesday.strftime('%B %d')}"
            }
        elif 'saturday' in text_lower and 'sunday' in text_lower:
            # Find next weekend
            days_until_saturday = (5 - today.weekday()) % 7
            if days_until_saturday == 0 and today.hour > 12:  # If it's Saturday afternoon, next weekend
                days_until_saturday = 7
            saturday = today + timedelta(days=days_until_saturday)
            sunday = saturday + timedelta(days=1)
            return {
                'success': True,
                'dates': [saturday.strftime('%Y-%m-%d'), sunday.strftime('%Y-%m-%d')],
                'dates_text': f"Saturday and Sunday, {saturday.strftime('%B %d')}-{sunday.strftime('%d')}"
            }
        
        return {
            'success': False,
            'error': 'Could not parse dates'
        }
