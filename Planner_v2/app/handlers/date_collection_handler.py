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
            message_text = message.strip()
            
            # Validate that the input looks like a date, not a menu selection or random text
            if not self._looks_like_date_input(message_text):
                return HandlerResult.error_response(
                    "Please enter dates for your event. Examples:\n"
                    "• 'Next Friday and Saturday'\n"
                    "• 'December 15-17'\n"
                    "• '8/1, 8/3, 8/5'\n"
                    "• 'Saturday'"
                )
            
            # Parse dates using AI for this step
            date_data = self._parse_date_input(message_text)
            
            if date_data['success']:
                # Save dates to event - store both individual dates and text summary
                import json
                dates_json = json.dumps(date_data['dates'])
                event.notes = f"Proposed dates: {date_data['dates_text']}\nDates JSON: {dates_json}"
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
        # For simple day combinations, try backup parser first (more reliable)
        text_lower = text.lower()
        simple_day_combos = [
            'friday and saturday', 'friday or saturday', 'saturday and friday', 'saturday or friday',
            'tuesday and wednesday', 'tuesday or wednesday', 'wednesday and tuesday', 'wednesday or tuesday'
        ]
        if any(combo in text_lower for combo in simple_day_combos):
            backup_result = self._simple_parse_dates(text)
            if backup_result and backup_result.get('success'):
                return backup_result
        
        # Use AI parsing as primary method for everything else
        ai_result = self._ai_parse_dates(text)
        if ai_result and ai_result.get('success'):
            return ai_result
        
        # If AI fails, try backup parser
        backup_result = self._simple_parse_dates(text)
        if backup_result and backup_result.get('success'):
            return backup_result
        
        # If both fail, return error
        return {'success': False, 'error': 'Could not parse dates'}
    
    def _ai_parse_dates(self, text: str) -> dict:
        """AI parsing for date collection step only"""
        try:
            today = datetime.now().strftime('%A, %B %d, %Y')
            
            prompt = f"""Parse dates from this user input: "{text}"
Today is {today}

CRITICAL INSTRUCTIONS:
1. Return ONLY valid JSON - no extra text, explanations, or formatting
2. Parse exactly what the user requested - do not add extra dates
3. ALWAYS look forward in time - never return dates in the past
4. Single day (e.g., "Tuesday") = return ONLY the NEXT occurrence of that day
5. "Monday and Tuesday" = return BOTH Monday AND Tuesday dates (next occurrences)
6. "Monday or Tuesday" = return BOTH Monday AND Tuesday dates (user wants options)
7. Date ranges with "-" include ALL dates between start and end inclusive

IMPORTANT: When user says a day name like "Saturday", they mean the NEXT Saturday, not the previous one.
If today is Sunday and user says "Saturday", return next Saturday (6 days ahead), not yesterday's Saturday.

Required JSON format:
{{"success": true, "dates": ["YYYY-MM-DD"], "dates_text": "readable description"}}

Examples for {today}:
"Friday" → {{"success": true, "dates": ["2025-08-15"], "dates_text": "Friday, August 15"}}
"Saturday" → {{"success": true, "dates": ["2025-08-16"], "dates_text": "Saturday, August 16"}}
"Monday and Tuesday" → {{"success": true, "dates": ["2025-08-11", "2025-08-12"], "dates_text": "Monday and Tuesday, August 11-12"}}
"8/11-8/14" → {{"success": true, "dates": ["2025-08-11", "2025-08-12", "2025-08-13", "2025-08-14"], "dates_text": "August 11-14"}}

RESPOND WITH ONLY THE JSON OBJECT - NO OTHER TEXT."""

            response = self.ai_service.make_completion(prompt, 300)
            if response and response.strip():
                try:
                    # Extract JSON from response - AI sometimes adds extra text
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        result = json.loads(json_str)
                        logger.info(f"Date collection AI parsing successful: {result}")
                        return result
                    else:
                        logger.error(f"No JSON found in AI response: '{response}'")
                except json.JSONDecodeError as je:
                    logger.error(f"Date collection JSON parsing error: {je}, Response: '{response}'")
            else:
                logger.error(f"Date collection AI returned empty response for input: '{text}'")
                
        except Exception as e:
            logger.error(f"Date collection AI parsing error: {e}")
            
        return None
    
    def _simple_parse_dates(self, text: str) -> dict:
        """Simple fallback for date collection step"""
        text_lower = text.lower().strip()
        today = datetime.now()
        
        # Check for date ranges like "8/11-8/14" or "8/11-8/14"
        range_pattern = r'(\d{1,2})/(\d{1,2})\s*-\s*(\d{1,2})/(\d{1,2})'
        range_match = re.search(range_pattern, text)
        if range_match:
            start_month, start_day, end_month, end_day = range_match.groups()
            try:
                start_date = datetime(today.year, int(start_month), int(start_day))
                end_date = datetime(today.year, int(end_month), int(end_day))
                
                # If start date is in the past, assume next year
                if start_date.date() < today.date():
                    start_date = start_date.replace(year=today.year + 1)
                    end_date = end_date.replace(year=today.year + 1)
                
                # Generate all dates in range
                dates = []
                current = start_date
                while current <= end_date:
                    dates.append(current.strftime('%Y-%m-%d'))
                    current += timedelta(days=1)
                
                return {
                    'success': True,
                    'dates': dates,
                    'dates_text': f"{start_date.strftime('%B %-d')}-{end_date.strftime('%-d')}"
                }
            except ValueError:
                pass  # Fall through to other parsing methods
        
        # Check for day-to-day ranges like "Friday to Monday" or "Tuesday to Friday"
        day_to_pattern = r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+to\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)'
        day_to_match = re.search(day_to_pattern, text_lower)
        if day_to_match:
            start_day, end_day = day_to_match.groups()
            return self._parse_day_range(start_day, end_day, today)
        
        # Check for multiple day combinations FIRST before individual days
        if 'saturday' in text_lower and 'sunday' in text_lower:
            # Both Saturday and Sunday mentioned
            days_until_saturday = (5 - today.weekday()) % 7
            if days_until_saturday == 0 and today.hour > 12:  # If it's Saturday afternoon, next weekend
                days_until_saturday = 7
            saturday = today + timedelta(days=days_until_saturday)
            sunday = saturday + timedelta(days=1)
            return {
                'success': True,
                'dates': [saturday.strftime('%Y-%m-%d'), sunday.strftime('%Y-%m-%d')],
                'dates_text': f"Saturday and Sunday, {saturday.strftime('%B %-d')}-{sunday.strftime('%-d')}"
            }
        elif 'monday' in text_lower and 'tuesday' in text_lower:
            # Both Monday and Tuesday mentioned
            next_monday = today + timedelta(days=(7 - today.weekday()) % 7)
            if next_monday.date() == today.date():  # If today is Monday
                next_monday = today + timedelta(days=7)
            next_tuesday = next_monday + timedelta(days=1)
            return {
                'success': True,
                'dates': [next_monday.strftime('%Y-%m-%d'), next_tuesday.strftime('%Y-%m-%d')],
                'dates_text': f"Monday and Tuesday, {next_monday.strftime('%B %-d')}-{next_tuesday.strftime('%-d')}"
            }
        elif ('tuesday' in text_lower and 'wednesday' in text_lower) or \
             ('tuesday' in text_lower and 'wednesday' in text_lower and ('and' in text_lower or 'or' in text_lower)):
            # Tuesday and Wednesday (including "Tuesday or Wednesday")
            next_tuesday = today + timedelta(days=((1 - today.weekday()) % 7))
            if next_tuesday.date() == today.date():  # If today is Tuesday
                next_tuesday = today + timedelta(days=7)
            next_wednesday = next_tuesday + timedelta(days=1)
            return {
                'success': True,
                'dates': [next_tuesday.strftime('%Y-%m-%d'), next_wednesday.strftime('%Y-%m-%d')],
                'dates_text': f"Tuesday and Wednesday, {next_tuesday.strftime('%B %-d')}-{next_wednesday.strftime('%-d')}"
            }
        elif ('friday' in text_lower and 'saturday' in text_lower) or \
             ('friday' in text_lower and 'saturday' in text_lower and ('and' in text_lower or 'or' in text_lower)):
            # Friday and Saturday (including "Friday or Saturday")
            next_friday = today + timedelta(days=((4 - today.weekday()) % 7))
            if next_friday.date() == today.date():  # If today is Friday
                next_friday = today + timedelta(days=7)
            next_saturday = next_friday + timedelta(days=1)
            return {
                'success': True,
                'dates': [next_friday.strftime('%Y-%m-%d'), next_saturday.strftime('%Y-%m-%d')],
                'dates_text': f"Friday and Saturday, {next_friday.strftime('%B %-d')}-{next_saturday.strftime('%-d')}"
            }
        # Handle single day mentions - do NOT expand into multiple days
        elif 'friday' in text_lower:
            # Find next Friday
            next_friday = today + timedelta(days=((4 - today.weekday()) % 7))
            if next_friday.date() == today.date():  # If today is Friday
                next_friday = today + timedelta(days=7)
            return {
                'success': True,
                'dates': [next_friday.strftime('%Y-%m-%d')],
                'dates_text': f"Friday, {next_friday.strftime('%B %-d')}"
            }
        elif 'saturday' in text_lower:
            # Find next Saturday
            days_until_saturday = (5 - today.weekday()) % 7
            if days_until_saturday == 0 and today.hour > 12:  # If it's Saturday afternoon, next Saturday
                days_until_saturday = 7
            saturday = today + timedelta(days=days_until_saturday)
            return {
                'success': True,
                'dates': [saturday.strftime('%Y-%m-%d')],
                'dates_text': f"Saturday, {saturday.strftime('%B %-d')}"
            }
        elif 'sunday' in text_lower:
            # Find next Sunday
            days_until_sunday = (6 - today.weekday()) % 7
            if days_until_sunday == 0 and today.hour > 12:  # If it's Sunday afternoon, next Sunday
                days_until_sunday = 7
            sunday = today + timedelta(days=days_until_sunday)
            return {
                'success': True,
                'dates': [sunday.strftime('%Y-%m-%d')],
                'dates_text': f"Sunday, {sunday.strftime('%B %-d')}"
            }
        elif 'monday' in text_lower:
            next_monday = today + timedelta(days=(7 - today.weekday()) % 7)
            if next_monday.date() == today.date():  # If today is Monday
                next_monday = today + timedelta(days=7)
            return {
                'success': True,
                'dates': [next_monday.strftime('%Y-%m-%d')],
                'dates_text': f"Monday, {next_monday.strftime('%B %-d')}"
            }
        elif 'tuesday' in text_lower:
            next_tuesday = today + timedelta(days=((1 - today.weekday()) % 7))
            if next_tuesday.date() == today.date():  # If today is Tuesday
                next_tuesday = today + timedelta(days=7)
            return {
                'success': True,
                'dates': [next_tuesday.strftime('%Y-%m-%d')],
                'dates_text': f"Tuesday, {next_tuesday.strftime('%B %-d')}"
            }
        elif 'wednesday' in text_lower:
            next_wednesday = today + timedelta(days=((2 - today.weekday()) % 7))
            if next_wednesday.date() == today.date():  # If today is Wednesday
                next_wednesday = today + timedelta(days=7)
            return {
                'success': True,
                'dates': [next_wednesday.strftime('%Y-%m-%d')],
                'dates_text': f"Wednesday, {next_wednesday.strftime('%B %-d')}"
            }
        elif 'thursday' in text_lower:
            next_thursday = today + timedelta(days=((3 - today.weekday()) % 7))
            if next_thursday.date() == today.date():  # If today is Thursday
                next_thursday = today + timedelta(days=7)
            return {
                'success': True,
                'dates': [next_thursday.strftime('%Y-%m-%d')],
                'dates_text': f"Thursday, {next_thursday.strftime('%B %-d')}"
            }
        
        return {
            'success': False,
            'error': 'Could not parse dates'
        }

    def _looks_like_date_input(self, text: str) -> bool:
        """Validate that input looks like a date, not a menu selection or random text"""
        text_lower = text.lower().strip()
        
        # Reject single digits or very short inputs that are likely menu selections
        if text_lower.isdigit() and len(text_lower) <= 2:
            return False
        
        # Reject common non-date inputs
        invalid_inputs = [
            'yes', 'no', 'ok', 'okay', 'hi', 'hello', 'hey', 'test', 'done',
            'next', 'back', 'cancel', 'skip', 'continue', 'restart'
        ]
        if text_lower in invalid_inputs:
            return False
        
        # Must contain date-related words, day names, month names, or date patterns
        date_indicators = [
            # Day names
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun',
            # Month names
            'january', 'february', 'march', 'april', 'may', 'june',
            'july', 'august', 'september', 'october', 'november', 'december',
            'jan', 'feb', 'mar', 'apr', 'may', 'jun',
            'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
            # Date words
            'today', 'tomorrow', 'yesterday', 'next', 'this', 'weekend',
            'week', 'day', 'date', 'time'
        ]
        
        # Check if input contains any date indicators
        if any(indicator in text_lower for indicator in date_indicators):
            return True
        
        # Check for date patterns (MM/DD, MM-DD, etc.)
        date_patterns = [
            r'\d{1,2}[/-]\d{1,2}',  # 12/15, 12-15
            r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',  # 12/15/24, 12-15-2024
            r'\d{1,2}\s+(to|through|thru|-)\s+\d{1,2}',  # 15 to 17, 15-17
        ]
        
        if any(re.search(pattern, text_lower) for pattern in date_patterns):
            return True
        
        # If input is longer than 3 characters and doesn't match invalid patterns, allow it
        # This catches things like "December 15th" that might not match exact patterns
        if len(text_lower) > 3 and not text_lower.isdigit():
            return True
        
        return False
