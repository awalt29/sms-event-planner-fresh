from typing import Optional
import logging
import os
import requests
import json

logger = logging.getLogger(__name__)

class AIProcessingService:
    """Lightweight AI client for handlers to use - HTTP-based to avoid library issues"""
    
    def __init__(self):
        """Initialize OpenAI HTTP client"""
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.base_url = "https://api.openai.com/v1"
        
        if not self.api_key:
            logger.error("OPENAI_API_KEY environment variable is required - AI features will be disabled")
            self.api_key = None  # Explicitly set to None for safety
        else:
            logger.info("AI Processing Service initialized with HTTP client")
    
    def make_completion(self, prompt: str, max_tokens: int = 200) -> Optional[str]:
        """Make a completion request via HTTP - handlers parse the response"""
        if not self.api_key:
            logger.error("No OpenAI API key available")
            return None
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "gpt-4o",  # Most capable GPT-4 model for complex parsing
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": max_tokens
            }
            
            # PERFORMANCE OPTIMIZATION: Reduced timeout from 30s to 8s
            # SMS users expect fast responses - better to fall back to regex parsing
            # than wait 30 seconds for AI. 8s is reasonable for most API calls.
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=8  # Reduced from 30s - fallback to simple parsing if slow
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content'].strip()
            else:
                logger.error(f"OpenAI API error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"OpenAI completion failed: {e}")
            return None
    
    def parse_time_input(self, time_text: str) -> dict:
        """Parse a time input like '3pm', '7:30pm', '6pm' into structured format"""
        if not self.api_key:
            # Fallback to simple parsing without AI
            return self._simple_time_parse(time_text)
        
        prompt = f"""
        Parse this time input into a structured format: "{time_text}"
        
        Return JSON with:
        {{
            "success": true/false,
            "start_hour": 24-hour format (0-23),
            "start_minute": minute (0-59),
            "original_text": "{time_text}"
        }}
        
        Examples:
        "3pm" → {{"success": true, "start_hour": 15, "start_minute": 0, "original_text": "3pm"}}
        "7:30pm" → {{"success": true, "start_hour": 19, "start_minute": 30, "original_text": "7:30pm"}}
        "6pm" → {{"success": true, "start_hour": 18, "start_minute": 0, "original_text": "6pm"}}
        "noon" → {{"success": true, "start_hour": 12, "start_minute": 0, "original_text": "noon"}}
        "midnight" → {{"success": true, "start_hour": 0, "start_minute": 0, "original_text": "midnight"}}
        
        If the input is unclear, return: {{"success": false, "original_text": "{time_text}"}}
        """
        
        try:
            response = self.make_completion(prompt, max_tokens=150)
            if response:
                # Parse the JSON response
                import json
                result = json.loads(response)
                return result
            else:
                return self._simple_time_parse(time_text)
        except Exception as e:
            logger.error(f"AI time parsing failed: {e}")
            return self._simple_time_parse(time_text)
    
    def _simple_time_parse(self, time_text: str) -> dict:
        """Simple fallback time parsing without AI"""
        import re
        
        text = time_text.lower().strip()
        
        # Common patterns
        patterns = [
            (r'(\d{1,2}):(\d{2})\s*([ap])m?', 'time_with_minutes'),
            (r'(\d{1,2})\s*([ap])m?', 'time_hour_only'),
            (r'noon', 'noon'),
            (r'midnight', 'midnight')
        ]
        
        for pattern, pattern_type in patterns:
            match = re.search(pattern, text)
            if match:
                if pattern_type == 'time_with_minutes':
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    am_pm = match.group(3)
                    
                    # Convert to 24-hour format
                    if am_pm == 'p' and hour != 12:
                        hour += 12
                    elif am_pm == 'a' and hour == 12:
                        hour = 0
                        
                    return {
                        "success": True,
                        "start_hour": hour,
                        "start_minute": minute,
                        "original_text": time_text
                    }
                elif pattern_type == 'time_hour_only':
                    hour = int(match.group(1))
                    am_pm = match.group(2)
                    
                    # Convert to 24-hour format
                    if am_pm == 'p' and hour != 12:
                        hour += 12
                    elif am_pm == 'a' and hour == 12:
                        hour = 0
                        
                    return {
                        "success": True,
                        "start_hour": hour,
                        "start_minute": 0,
                        "original_text": time_text
                    }
                elif pattern_type == 'noon':
                    return {
                        "success": True,
                        "start_hour": 12,
                        "start_minute": 0,
                        "original_text": time_text
                    }
                elif pattern_type == 'midnight':
                    return {
                        "success": True,
                        "start_hour": 0,
                        "start_minute": 0,
                        "original_text": time_text
                    }
        
        return {
            "success": False,
            "original_text": time_text
        }