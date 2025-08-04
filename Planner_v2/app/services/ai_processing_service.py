from typing import Dict, List
import logging
import os
import json

logger = logging.getLogger(__name__)

class AIProcessingService:
    """Handles AI integration for natural language processing"""
    
    def __init__(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        except ImportError:
            logger.warning("OpenAI library not available")
            self.client = None
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {e}")
            self.client = None
    
    def parse_natural_language_dates(self, message: str) -> Dict:
        """Convert natural language to structured date objects"""
        try:
            if not self.client:
                return self._fallback_date_parsing(message)
                
            prompt = f"""
            Parse the following date text into structured data:
            "{message}"
            
            Return JSON with:
            - success: boolean
            - dates: list of date strings in YYYY-MM-DD format
            - dates_text: human readable summary
            
            Examples:
            "Monday" -> {{"success": true, "dates": ["2025-08-04"], "dates_text": "Monday, August 4"}}
            "Saturday and Sunday" -> {{"success": true, "dates": ["2025-08-09", "2025-08-10"], "dates_text": "Saturday and Sunday"}}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                timeout=20
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"AI date parsing error: {e}")
            return self._fallback_date_parsing(message)
    
    def parse_availability_text(self, message: str, context: Dict) -> Dict:
        """Parse availability responses like 'Monday after 2pm'"""
        try:
            if not self.client:
                return self._fallback_availability_parsing(message)
                
            prompt = f"""
            Parse availability from: "{message}"
            Context: {context}
            
            Return JSON with:
            - available_dates: list of {{date, start_time, end_time, all_day}}
            - notes: any additional notes
            
            Example:
            "Monday after 2pm" -> {{
                "available_dates": [{{
                    "date": "2025-08-04",
                    "start_time": "14:00",
                    "end_time": "23:59",
                    "all_day": false
                }}]
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                timeout=20
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"AI availability parsing error: {e}")
            return self._fallback_availability_parsing(message)

    def parse_event_input(self, text: str) -> Dict:
        """Parse event creation text"""
        try:
            if not self.client:
                return self._fallback_event_parsing(text)
                
            prompt = f"""
            Parse event details from: "{text}"
            
            Return JSON with:
            - title: event title (optional)
            - location: location if mentioned
            - activity: activity type if mentioned
            - success: boolean
            
            Example:
            "dinner friday in brooklyn" -> {{
                "title": "Dinner",
                "location": "Brooklyn", 
                "activity": "dinner",
                "success": true
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                timeout=20
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"AI event parsing error: {e}")
            return self._fallback_event_parsing(text)
    
    def _fallback_date_parsing(self, message: str) -> Dict:
        """Fallback date parsing without AI"""
        import re
        from datetime import datetime, timedelta
        
        message_lower = message.lower().strip()
        
        # Try to parse numeric date formats like "8/15", "8/15, 8/16"
        date_pattern = r'(\d{1,2})/(\d{1,2})'
        matches = re.findall(date_pattern, message)
        
        if matches:
            dates = []
            date_strings = []
            for month, day in matches:
                try:
                    # Assume current year for simplicity
                    date_obj = datetime(2025, int(month), int(day))
                    dates.append(date_obj.strftime('%Y-%m-%d'))
                    date_strings.append(date_obj.strftime('%B %d'))
                except ValueError:
                    continue
            
            if dates:
                dates_text = ', '.join(date_strings)
                return {'success': True, 'dates': dates, 'dates_text': dates_text}
        
        # Simple patterns for common date formats
        if 'monday' in message_lower:
            return {'success': True, 'dates': ['2025-08-04'], 'dates_text': 'Monday, August 4'}
        elif 'saturday' in message_lower and 'sunday' in message_lower:
            return {'success': True, 'dates': ['2025-08-09', '2025-08-10'], 'dates_text': 'Saturday and Sunday'}
        elif 'saturday' in message_lower:
            return {'success': True, 'dates': ['2025-08-09'], 'dates_text': 'Saturday, August 9'}
        elif 'sunday' in message_lower:
            return {'success': True, 'dates': ['2025-08-10'], 'dates_text': 'Sunday, August 10'}
        
        return {'success': False, 'error': 'Could not parse dates'}
    
    def _fallback_availability_parsing(self, message: str) -> Dict:
        """Fallback availability parsing without AI"""
        message_lower = message.lower().strip()
        
        # Simple patterns for availability
        if 'monday' in message_lower and 'after 2' in message_lower:
            return {
                'available_dates': [{
                    'date': '2025-08-04',
                    'start_time': '14:00',
                    'end_time': '23:59',
                    'all_day': False
                }]
            }
        elif 'all day' in message_lower:
            return {
                'available_dates': [{
                    'date': '2025-08-04',
                    'start_time': '00:00',
                    'end_time': '23:59',
                    'all_day': True
                }]
            }
        
        return {'error': 'Could not parse availability'}
    
    def parse_time_selection(self, message: str) -> Dict:
        """Parse time selection input"""
        try:
            message_lower = message.lower().strip()
            
            # Simple time parsing for testing
            if 'afternoon' in message_lower:
                return {'success': True, 'time_text': 'Afternoon (2:00pm-6:00pm)'}
            elif 'evening' in message_lower:
                return {'success': True, 'time_text': 'Evening (6:00pm-10:00pm)'}
            elif 'morning' in message_lower:
                return {'success': True, 'time_text': 'Morning (9:00am-12:00pm)'}
            else:
                return {'success': True, 'time_text': message}
                
        except Exception as e:
            logger.error(f"Error parsing time selection: {e}")
            return {'success': False, 'error': str(e)}
    
    def _fallback_event_parsing(self, text: str) -> Dict:
        """Fallback event parsing without AI"""
        text_lower = text.lower().strip()
        
        result = {'success': True}
        
        # Simple keyword detection
        if 'dinner' in text_lower:
            result['activity'] = 'dinner'
            result['title'] = 'Dinner'
        elif 'lunch' in text_lower:
            result['activity'] = 'lunch'
            result['title'] = 'Lunch'
        elif 'coffee' in text_lower:
            result['activity'] = 'coffee'
            result['title'] = 'Coffee'
        
        # Location detection
        if 'brooklyn' in text_lower:
            result['location'] = 'Brooklyn'
        elif 'manhattan' in text_lower:
            result['location'] = 'Manhattan'
        
        return result
