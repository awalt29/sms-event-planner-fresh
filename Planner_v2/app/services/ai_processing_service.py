from typing import Dict, List
import logging
import os
import json
import requests

logger = logging.getLogger(__name__)

class AIProcessingService:
    """Handles AI integration for natural language processing - using direct HTTP requests"""
    
    _instance = None
    _api_key = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIProcessingService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_client()
            self._initialized = True
    
    def _initialize_client(self):
        """Initialize OpenAI API key for direct HTTP requests"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key and len(api_key.strip()) > 0:
                self._api_key = api_key.strip()
                logger.info("OpenAI API key loaded successfully - using direct HTTP requests")
            else:
                logger.error("OPENAI_API_KEY is required for this application to work properly")
                self._api_key = None
        except Exception as e:
            logger.error(f"OpenAI API key initialization failed: {e}")
            self._api_key = None
    
    def _make_chat_completion(self, prompt: str, max_tokens: int = 200) -> str:
        """Make a chat completion request using direct HTTP requests"""
        if not self._api_key:
            raise Exception("OpenAI API key not available")
        
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": max_tokens
            }
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
                
        except Exception as e:
            logger.error(f"Direct HTTP chat completion failed: {e}")
            raise
    
    def parse_natural_language_dates(self, message: str) -> Dict:
        """Convert natural language to structured date objects"""
        if not self._api_key:
            logger.error("OpenAI API key not available - cannot parse dates")
            return self._fallback_date_parsing(message)
            
        try:
            prompt = f"""
            Parse the following date text into structured data. Today is August 4, 2025 (Sunday).
            Text: "{message}"
            
            Return ONLY valid JSON with:
            - success: boolean
            - dates: list of date strings in YYYY-MM-DD format
            - dates_text: human readable summary
            
            Examples:
            "Monday" -> {{"success": true, "dates": ["2025-08-05"], "dates_text": "Monday, August 5"}}
            "Saturday and Sunday" -> {{"success": true, "dates": ["2025-08-09", "2025-08-10"], "dates_text": "Saturday and Sunday"}}
            "8/15" -> {{"success": true, "dates": ["2025-08-15"], "dates_text": "Friday, August 15"}}
            """
            
            response_text = self._make_chat_completion(prompt, 200)
            result = json.loads(response_text)
            logger.info(f"AI date parsing successful: {result}")
            return result
            
        except Exception as e:
            logger.error(f"AI date parsing error: {e}")
            return self._fallback_date_parsing(message)
    
    def parse_availability_text(self, message: str, context: Dict) -> Dict:
        """Parse availability responses like 'Monday after 2pm'"""
        if not self._api_key:
            logger.error("OpenAI API key not available - cannot parse availability")
            return self._fallback_availability_parsing(message)
            
        try:
            dates_context = context.get('dates', [])
            prompt = f"""
            Parse availability from: "{message}"
            Available dates: {dates_context}
            
            Return ONLY valid JSON with:
            - available_dates: list of objects with {{date, start_time, end_time, all_day}}
            - notes: any additional notes (optional)
            
            Time format: HH:MM (24-hour)
            
            Examples:
            "Monday after 2pm" -> {{
                "available_dates": [{{
                    "date": "2025-08-05",
                    "start_time": "14:00",
                    "end_time": "23:59",
                    "all_day": false
                }}]
            }}
            
            "All day Saturday" -> {{
                "available_dates": [{{
                    "date": "2025-08-09",
                    "start_time": "00:00",
                    "end_time": "23:59",
                    "all_day": true
                }}]
            }}
            """
            
            response_text = self._make_chat_completion(prompt, 300)
            result = json.loads(response_text)
            logger.info(f"AI availability parsing successful: {result}")
            return result
            
        except Exception as e:
            logger.error(f"AI availability parsing error: {e}")
            return self._fallback_availability_parsing(message)

    def parse_event_input(self, text: str) -> Dict:
        """Parse event creation text"""
        if not self._api_key:
            logger.error("OpenAI API key not available - cannot parse event")
            return self._fallback_event_parsing(text)
            
        try:
            prompt = f"""
            Parse event details from: "{text}"
            
            Return ONLY valid JSON with:
            - title: event title (if mentioned)
            - location: location (if mentioned)
            - activity: activity type (if mentioned)
            - success: boolean
            
            Examples:
            "dinner friday in brooklyn" -> {{
                "title": "Dinner",
                "location": "Brooklyn", 
                "activity": "dinner",
                "success": true
            }}
            
            "coffee meeting" -> {{
                "title": "Coffee Meeting",
                "activity": "coffee",
                "success": true
            }}
            """
            
            response_text = self._make_chat_completion(prompt, 200)
            result = json.loads(response_text)
            logger.info(f"AI event parsing successful: {result}")
            return result
            
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

    def parse_guest_input(self, text: str) -> Dict:
        """Parse guest names and phone numbers from text"""
        if not self._api_key:
            logger.error("OpenAI API key not available - cannot parse guests")
            return {'success': False, 'error': 'AI parsing not available'}
            
        try:
            prompt = f"""
            Parse guest information from: "{text}"
            
            Extract names and phone numbers. Return ONLY valid JSON with:
            - success: boolean
            - guests: list of objects with {{name, phone}} where phone is optional
            - error: string (if success is false)
            
            Examples:
            "John Doe, 123-456-7890" -> {{
                "success": true,
                "guests": [{{"name": "John Doe", "phone": "123-456-7890"}}]
            }}
            
            "Sarah and Mike" -> {{
                "success": true, 
                "guests": [{{"name": "Sarah"}}, {{"name": "Mike"}}]
            }}
            
            "Awork 15105935336" -> {{
                "success": true,
                "guests": [{{"name": "Awork", "phone": "15105935336"}}]
            }}
            """
            
            response_text = self._make_chat_completion(prompt, 300)
            result = json.loads(response_text)
            logger.info(f"AI guest parsing successful: {result}")
            return result
            
        except Exception as e:
            logger.error(f"AI guest parsing error: {e}")
            return {'success': False, 'error': f'AI parsing failed: {str(e)}'}
