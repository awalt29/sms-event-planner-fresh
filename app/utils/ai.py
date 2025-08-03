from openai import OpenAI
from flask import current_app
import json
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class AIService:
    """Service class for handling AI operations with OpenAI."""
    
    def __init__(self):
        self.client = None
    
    def _initialize_client(self):
        """Initialize OpenAI client with configuration."""
        try:
            api_key = current_app.config.get('OPENAI_API_KEY')
            
            if not api_key or len(api_key) < 20:  # Check for missing or too short key
                logger.warning("OpenAI API key not properly configured")
                return  # Skip initialization but don't raise error
            
            self.client = OpenAI(api_key=api_key)
            logger.info("OpenAI client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None  # Set to None instead of raising
    
    def should_use_gpt_parsing(self, text: str, context_status: Optional[str] = None) -> bool:
        """
        Determine if GPT should be used for parsing complex input.
        
        Args:
            text: Input text to analyze
            context_status: Current context/status of the conversation
            
        Returns:
            bool: Whether to use GPT parsing
        """
        # Use GPT for complex natural language inputs
        complex_indicators = [
            'maybe', 'might', 'could', 'possibly', 'prefer', 'would like',
            'around', 'approximately', 'between', 'either', 'or',
            'depends', 'flexible', 'open to', 'not sure'
        ]
        
        # Use GPT for date/time parsing
        time_indicators = [
            'morning', 'afternoon', 'evening', 'night', 'weekend',
            'next week', 'this week', 'tomorrow', 'today',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
        ]
        
        text_lower = text.lower()
        
        # Check for complex language
        has_complex_language = any(indicator in text_lower for indicator in complex_indicators)
        has_time_language = any(indicator in text_lower for indicator in time_indicators)
        
        # Use GPT if text is long or complex
        is_long_text = len(text.split()) > 10
        
        return has_complex_language or has_time_language or is_long_text
    
    def parse_event_input(self, text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Parse natural language input for event details.
        
        Args:
            text: Natural language input
            context: Additional context for parsing
            
        Returns:
            dict: Parsed event information
        """
        try:
            if not self.client:
                self._initialize_client()
            
            # If OpenAI is not available, return a simple default response
            if not self.client:
                logger.info("OpenAI not available, using fallback event creation")
                return {
                    "title": "Hangout", 
                    "description": text,
                    "confidence": "low"
                }
            
            system_prompt = """
            You are an event planning assistant. Parse the user's input and extract event details.
            Return a JSON object with the following structure:
            {
                "title": "event title",
                "description": "event description",
                "activity": "activity type",
                "date": "parsed date (YYYY-MM-DD format if specific)",
                "time": "parsed time (HH:MM format if specific)",
                "duration": "duration in hours (number)",
                "location": "location/venue",
                "guest_count": "estimated number of guests",
                "budget": "budget amount (number)",
                "special_requirements": ["list", "of", "requirements"],
                "confidence": "confidence level (high/medium/low)"
            }
            
            Only include fields that can be clearly determined from the input.
            If information is ambiguous or missing, don't include that field.
            """
            
            user_prompt = f"Parse this event request: {text}"
            
            if context:
                user_prompt += f"\n\nAdditional context: {json.dumps(context)}"
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Event parsing successful: {result.get('confidence', 'unknown')} confidence")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse event input: {e}")
            # Return a fallback response instead of error
            return {
                "title": "Hangout",
                "description": text,
                "confidence": "low"
            }
    
    def parse_availability(self, text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Parse natural language availability input.
        
        Args:
            text: Natural language availability description
            context: Additional context for parsing
            
        Returns:
            dict: Parsed availability information
        """
        try:
            if not self.client:
                self._initialize_client()
            
            system_prompt = """
            You are parsing availability information for an event. Extract available time slots from the user's input.
            Return a JSON object with this structure:
            {
                "available_dates": [
                    {
                        "date": "YYYY-MM-DD",
                        "start_time": "HH:MM",
                        "end_time": "HH:MM",
                        "all_day": true/false,
                        "preference": "preferred/available/reluctant"
                    }
                ],
                "unavailable_dates": ["YYYY-MM-DD", ...],
                "notes": "additional notes or constraints",
                "confidence": "high/medium/low"
            }
            
            IMPORTANT: When parsing relative dates (like "Saturday", "Sunday"), use the context of the proposed event dates.
            If the event context mentions specific dates, map day names to those dates.
            For example, if event notes mention "Saturday, August 2, Sunday, August 3", then:
            - "Saturday" should map to "2025-08-02"
            - "Sunday" should map to "2025-08-03"
            """
            
            user_prompt = f"Parse this availability: {text}"
            
            if context:
                user_prompt += f"\n\nContext: {json.dumps(context)}"
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Availability parsing successful: {result.get('confidence', 'unknown')} confidence")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to parse availability: {e}")
            return {"error": str(e), "confidence": "low"}
    
    def suggest_venues(self, activity: str, location: str, requirements: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get AI-powered venue suggestions.
        
        Args:
            activity: Type of activity/event
            location: General location/area
            requirements: List of special requirements
            
        Returns:
            dict: Venue suggestions and recommendations
        """
        try:
            # Initialize client if needed
            if self.client is None:
                self._initialize_client()
            
            if self.client is None:
                logger.warning("OpenAI client not available for venue suggestions")
                return {
                    "success": False,
                    "error": "AI service not available",
                    "venues": []
                }
            
            system_prompt = """
            You are a venue recommendation assistant. Suggest 5 specific, real venues for the given activity and location.
            When requirements mention "different from" certain venues, provide completely different options with different styles, price points, or vibes.
            When requirements mention "alternative style venues" or "different price range options", diversify your suggestions significantly.
            
            Return a JSON object with this exact structure:
            {
                "success": true,
                "venues": [
                    {
                        "name": "specific venue name",
                        "link": "venue website URL if known, otherwise leave blank",
                        "description": "brief description of why this venue works for the activity"
                    }
                ]
            }
            
            Focus on real, specific venues in the exact location mentioned. Include actual restaurant/bar names, not generic suggestions.
            For the link field: Only include the venue's actual website URL if you know it. If you don't know the website, leave the link field as an empty string "".
            Do NOT create Google Maps URLs - leave link empty if you don't know the actual website.
            
            If asked for different options, vary by: price range (budget/mid-range/upscale), cuisine type, ambiance (casual/trendy/traditional), location within the area.
            """
            
            requirements_text = f" with requirements: {', '.join(requirements)}" if requirements else ""
            user_prompt = f"Suggest 5 specific real venues for {activity} in {location}{requirements_text}"
            
            # Use higher temperature for more varied results when requirements specify "different"
            temperature = 0.9 if requirements and any("different" in req.lower() for req in requirements) else 0.7
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Venue suggestions generated for {activity} in {location}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate venue suggestions: {e}")
            return {
                "success": False,
                "error": str(e),
                "venues": []
            }
    
    def suggest_central_location(self, guest_locations: List[str]) -> Dict[str, Any]:
        """
        Suggest central meeting locations based on guest locations.
        
        Args:
            guest_locations: List of guest location descriptions
            
        Returns:
            dict: Central location suggestions
        """
        try:
            system_prompt = """
            You are a location optimization assistant. Given a list of guest locations,
            suggest central meeting points that minimize travel for everyone.
            Return a JSON object with this structure:
            {
                "suggested_locations": [
                    {
                        "location": "suggested area/city",
                        "reasoning": "why this location works well",
                        "estimated_travel_times": "general travel time estimates"
                    }
                ],
                "transportation_tips": "advice about transportation options"
            }
            
            Consider geographic proximity and transportation accessibility.
            """
            
            locations_text = ", ".join(guest_locations)
            user_prompt = f"Find central location for guests from: {locations_text}"
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Central location suggestions generated for {len(guest_locations)} locations")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to suggest central location: {e}")
            return {"error": str(e)}


# Global AI service instance (initialized lazily)
_ai_service = None


def get_ai_service():
    """Get or create AI service instance."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


def parse_event_input(text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Convenience function for parsing event input."""
    return get_ai_service().parse_event_input(text, context)


def parse_availability(text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Convenience function for parsing availability."""
    return get_ai_service().parse_availability(text, context)


def suggest_venues(activity: str, location: str, requirements: Optional[List[str]] = None) -> Dict[str, Any]:
    """Convenience function for venue suggestions."""
    return get_ai_service().suggest_venues(activity, location, requirements)


def suggest_central_location(guest_locations: List[str]) -> Dict[str, Any]:
    """Convenience function for central location suggestions."""
    return get_ai_service().suggest_central_location(guest_locations)


def fallback_date_parsing(text: str) -> Dict[str, Any]:
    """
    Simple fallback date parsing when AI is unavailable.
    """
    from datetime import datetime, timedelta
    import re
    
    try:
        # Handle simple date ranges like "8/1-8/3"
        range_match = re.search(r'(\d{1,2})/(\d{1,2})-(\d{1,2})/(\d{1,2})', text)
        if range_match:
            start_month, start_day, end_month, end_day = map(int, range_match.groups())
            current_year = datetime.now().year
            
            start_date = datetime(current_year, start_month, start_day)
            end_date = datetime(current_year, end_month, end_day)
            
            dates = []
            date_descriptions = []
            current = start_date
            
            while current <= end_date:
                dates.append(current.strftime('%Y-%m-%d'))
                day_name = current.strftime('%A')
                month_day = current.strftime('%B %d')
                date_descriptions.append(f"{day_name}, {month_day}")
                current += timedelta(days=1)
            
            return {
                "success": True,
                "dates": dates,
                "dates_text": ", ".join(date_descriptions),
                "date_range": {
                    "start": start_date.strftime('%Y-%m-%d'),
                    "end": end_date.strftime('%Y-%m-%d')
                },
                "confidence": "medium"
            }
        
        # Handle simple range like "8/1-8/3" (same month)
        simple_range_match = re.search(r'(\d{1,2})/(\d{1,2})-(\d{1,2})', text)
        if simple_range_match:
            month, start_day, end_day = map(int, simple_range_match.groups())
            current_year = datetime.now().year
            
            start_date = datetime(current_year, month, start_day)
            end_date = datetime(current_year, month, end_day)
            
            dates = []
            date_descriptions = []
            current = start_date
            
            while current <= end_date:
                dates.append(current.strftime('%Y-%m-%d'))
                day_name = current.strftime('%A')
                month_day = current.strftime('%B %d')
                date_descriptions.append(f"{day_name}, {month_day}")
                current += timedelta(days=1)
            
            return {
                "success": True,
                "dates": dates,
                "dates_text": ", ".join(date_descriptions),
                "date_range": {
                    "start": start_date.strftime('%Y-%m-%d'),
                    "end": end_date.strftime('%Y-%m-%d')
                },
                "confidence": "medium"
            }
        
        # Default fallback
        return {
            "success": True,
            "dates": [],
            "dates_text": text,
            "confidence": "low"
        }
        
    except Exception as e:
        logger.error(f"Fallback date parsing failed: {e}")
        return {
            "success": True,
            "dates": [],
            "dates_text": text,
            "confidence": "low"
        }


def parse_dates_from_text(text: str) -> Dict[str, Any]:
    """
    Parse date information from natural language text.
    
    Args:
        text: Natural language date description
        
    Returns:
        dict: Parsed date information
    """
    from datetime import datetime
    
    try:
        ai_service = get_ai_service()
        if not ai_service.client:
            ai_service._initialize_client()
        
        # If OpenAI is not available, use fallback parsing
        if not ai_service.client:
            logger.info("OpenAI not available, using fallback date parsing")
            return fallback_date_parsing(text)
        
        system_prompt = f"""
        You are parsing date information for event planning. You MUST get the day-of-week calculations correct.
        
        CRITICAL REFERENCE POINTS:
        - Today is {datetime.now().strftime('%B %d, %Y')} which is a {datetime.now().strftime('%A')}
        - August 1, 2025 is a {datetime(2025, 8, 1).strftime('%A')}
        - August 2, 2025 is a {datetime(2025, 8, 2).strftime('%A')}  
        - August 3, 2025 is a {datetime(2025, 8, 3).strftime('%A')}
        - August 4, 2025 is a {datetime(2025, 8, 4).strftime('%A')}
        
        For the input "8/1-8/3", you must return:
        - dates: ["2025-08-01", "2025-08-02", "2025-08-03"]
        - dates_text: "{datetime(2025, 8, 1).strftime('%A')}, August 1, {datetime(2025, 8, 2).strftime('%A')}, August 2, {datetime(2025, 8, 3).strftime('%A')}, August 3"
        
        Return JSON with this exact structure:
        {{
            "success": true,
            "dates": ["YYYY-MM-DD", ...],
            "dates_text": "Day, Month Date, Day, Month Date, ...",
            "date_range": {{
                "start": "YYYY-MM-DD",
                "end": "YYYY-MM-DD"
            }},
            "confidence": "high"
        }}
        
        Parse ranges like "8/1-8/3" to individual dates. Use 2025 as year if not specified.
        DOUBLE-CHECK your day-of-week calculations against the reference points above.
        """
        
        response = ai_service.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Parse these dates: {text}"}
            ],
            temperature=0.3
        )
        
        result = json.loads(response.choices[0].message.content)
        logger.info(f"Date parsing successful: {result.get('confidence', 'unknown')} confidence")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to parse dates: {e}")
        return {
            "success": False,
            "error": str(e),
            "confidence": "low"
        }
