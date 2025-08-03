from openai import OpenAI
from flask import current_app
import json
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# Log OpenAI version for debugging
try:
    import openai
    logger.info(f"OpenAI library version: {openai.__version__}")
except Exception as e:
    logger.error(f"Error checking OpenAI version: {e}")


class AIService:
    """Service class for handling AI operations with OpenAI."""
    
    def __init__(self):
        self.client = None
    
    def _initialize_client(self):
        """Initialize OpenAI client with configuration."""
        try:
            api_key = current_app.config.get('OPENAI_API_KEY')
            
            if not api_key:
                logger.error("OPENAI_API_KEY not found in configuration")
                self.client = None
                return
            
            if len(api_key) < 20:  # Check for too short key
                logger.error(f"OpenAI API key appears to be invalid (length: {len(api_key)})")
                self.client = None
                return
            
            # Detailed logging for debugging
            logger.info("Attempting to initialize OpenAI client...")
            logger.info(f"API key length: {len(api_key)}")
            logger.info(f"API key prefix: {api_key[:10]}...")
            
            # Try to create client with ONLY api_key parameter to avoid conflicts
            self.client = OpenAI(api_key=api_key)
            logger.info("OpenAI client created successfully")
            
            # Test the client with a simple request to verify it works
            try:
                test_response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Say 'test'"}],
                    max_tokens=5,
                    timeout=10
                )
                logger.info("OpenAI client test successful - API is working")
                
            except Exception as test_error:
                logger.error(f"OpenAI client test failed: {test_error}")
                logger.error(f"Test error type: {type(test_error).__name__}")
                # Still keep the client - maybe it's just a temporary network issue
                # Don't set client to None here, let individual requests handle failures
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Will use fallback parsing instead")
            self.client = None
    
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
            logger.error(f"Failed to parse availability with OpenAI: {e}")
            # Return fallback parsing for common availability formats
            return self._fallback_availability_parsing(text, context)
    
    def suggest_venues(self, activity: str, location: str, requirements: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get AI-powered venue suggestions with fallback to curated suggestions.
        
        Args:
            activity: Type of activity/event (e.g., "chinese food", "restaurant", "bar")
            location: General location/area
            requirements: List of special requirements
            
        Returns:
            dict: Venue suggestions with intelligent fallback handling
        """
        try:
            logger.info(f"Suggesting venues for '{activity}' in '{location}'")
            
            # Initialize client if needed
            if self.client is None:
                self._initialize_client()
            
            if self.client is None:
                logger.error("OpenAI client not available - using fallback")
                return self._create_fallback_venue_suggestions(activity, location)
            
            # Create optimized prompt for speed and accuracy
            prompt = f"""Suggest exactly 3 popular venues for "{activity}" in {location}.

Return ONLY this JSON format:
{{
  "venues": [
    {{"name": "Venue Name", "description": "Brief description"}},
    {{"name": "Venue Name", "description": "Brief description"}},
    {{"name": "Venue Name", "description": "Brief description"}}
  ]
}}

Requirements:
- Focus on well-known, popular places that actually exist
- Keep descriptions under 8 words
- Real venues in {location} area
- Exactly 3 venues, no more, no less
- No explanatory text, just the JSON"""
            
            if requirements:
                prompt += f"\n- Additional requirements: {', '.join(requirements)}"
            
            # Use GPT-3.5-turbo with very generous timeout for broad terms
            logger.info("Making OpenAI API request...")
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.7,
                timeout=30  # Very generous timeout - give OpenAI the best chance
            )
            
            content = response.choices[0].message.content.strip()
            logger.info(f"OpenAI response received successfully: {len(content)} characters")
            
            # Parse JSON response
            try:
                venues_data = json.loads(content)
                logger.info("JSON parsing successful")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse OpenAI JSON response: {e}")
                logger.error(f"Raw response: {content}")
                return self._create_fallback_venue_suggestions(activity, location)
            
            venues = venues_data.get('venues', [])
            
            # Ensure we have exactly 3 venues
            if len(venues) < 3:
                logger.warning(f"Only got {len(venues)} venues, creating fallback suggestions")
                return self._create_fallback_venue_suggestions(activity, location)
            elif len(venues) > 3:
                venues = venues[:3]  # Trim to exactly 3
            
            # Add Google Maps search links to each venue
            for venue in venues:
                venue_name = venue.get('name', '').replace(' ', '+')
                activity_clean = activity.replace(' ', '+')
                location_clean = location.replace(' ', '+')
                venue['link'] = f"https://www.google.com/maps/search/{venue_name}+{activity_clean}+{location_clean}"
            
            logger.info(f"Successfully generated {len(venues)} venue suggestions")
            return {
                'success': True,
                'venues': venues
            }
            
        except Exception as e:
            logger.error(f"Error suggesting venues with OpenAI: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return self._create_fallback_venue_suggestions(activity, location)

    def _create_fallback_venue_suggestions(self, activity: str, location: str) -> Dict[str, Any]:
        """
        Create intelligent venue suggestions when AI fails or is unavailable.
        Uses curated lists of popular venues by activity type and location.
        
        Args:
            activity: The activity description
            location: The location for the event
            
        Returns:
            dict: Success status with real venue suggestions
        """
        try:
            # Convert activity to a standardized format for venue matching
            activity_lower = activity.lower().strip()
            location_lower = location.lower().strip()
            
            # Curated venue suggestions by activity and location
            venue_database = {
                'chinese restaurant': {
                    'brooklyn': [
                        {"name": "L'industrie Pizzeria", "description": "Popular pizza spot"},
                        {"name": "Cecconi's Dumbo", "description": "Italian with Manhattan views"},
                        {"name": "Juliana's", "description": "Coal oven pizza"}
                    ],
                    'manhattan': [
                        {"name": "Joe's Shanghai", "description": "Famous soup dumplings"},
                        {"name": "Xi'an Famous Foods", "description": "Hand-pulled noodles"},
                        {"name": "Nom Wah Tea Parlor", "description": "Historic dim sum"}
                    ],
                    'new york': [
                        {"name": "Joe's Shanghai", "description": "Famous soup dumplings"},
                        {"name": "Xi'an Famous Foods", "description": "Hand-pulled noodles"},
                        {"name": "Nom Wah Tea Parlor", "description": "Historic dim sum"}
                    ],
                    'default': [
                        {"name": "Local Chinese Restaurant", "description": "Popular neighborhood spot"},
                        {"name": "Family Chinese Kitchen", "description": "Authentic Chinese cuisine"},
                        {"name": "Golden Dragon", "description": "Traditional Chinese dining"}
                    ]
                },
                'bar or cocktail lounge': {
                    'brooklyn': [
                        {"name": "House of Yes", "description": "Creative cocktails & performance"},
                        {"name": "Maison Premiere", "description": "Oysters & absinthe"},
                        {"name": "Lucinda Sterling", "description": "Natural wine bar"}
                    ],
                    'manhattan': [
                        {"name": "Death & Co", "description": "Craft cocktail pioneer"},
                        {"name": "Please Don't Tell", "description": "Hidden speakeasy"},
                        {"name": "Employees Only", "description": "Classic cocktail bar"}
                    ],
                    'default': [
                        {"name": "Local Sports Bar", "description": "Casual drinks & games"},
                        {"name": "Neighborhood Pub", "description": "Friendly local hangout"},
                        {"name": "Craft Cocktail Lounge", "description": "Creative mixed drinks"}
                    ]
                },
                'restaurant': {
                    'default': [
                        {"name": "Popular Local Restaurant", "description": "Highly rated neighborhood spot"},
                        {"name": "Family Restaurant", "description": "Casual dining favorite"},
                        {"name": "Trendy Bistro", "description": "Modern American cuisine"}
                    ]
                }
            }
            
            # Find the best match for the activity
            venues = None
            for activity_key in venue_database.keys():
                if activity_key in activity_lower or any(word in activity_lower for word in activity_key.split()):
                    venue_set = venue_database[activity_key]
                    # Try to match location
                    for location_key in venue_set.keys():
                        if location_key in location_lower or location_key == 'default':
                            venues = venue_set[location_key]
                            break
                    if venues:
                        break
            
            # If no specific match found, use generic restaurant suggestions
            if not venues:
                venues = venue_database['restaurant']['default']
                # Customize for the specific activity
                venues = [
                    {"name": f"Local {activity.title()}", "description": f"Popular {activity} spot"},
                    {"name": f"{location.title()} Favorite", "description": f"Well-reviewed {activity}"},
                    {"name": f"Neighborhood {activity.title()}", "description": f"Casual {activity} option"}
                ]
            
            # Add Google Maps search links
            activity_clean = activity.replace(' ', '+')
            location_clean = location.replace(' ', '+')
            
            for i, venue in enumerate(venues):
                venue_name_clean = venue['name'].replace(' ', '+')
                venue['link'] = f"https://www.google.com/maps/search/{venue_name_clean}+{location_clean}"
            
            return {
                'success': True,
                'venues': venues[:3]  # Return top 3
            }
            
        except Exception as e:
            logger.error(f"Error creating fallback suggestions: {e}")
            # Last resort - return search links with more specific names
            activity_clean = activity.replace(' ', '+')
            location_clean = location.replace(' ', '+')
            
            venues = [
                {
                    "name": f"Top-rated {activity} places",
                    "description": f"Find highly reviewed options",
                    "link": f"https://www.google.com/maps/search/top+rated+{activity_clean}+{location_clean}"
                },
                {
                    "name": f"Recommended {activity} spots",
                    "description": f"Discover popular choices",
                    "link": f"https://www.google.com/maps/search/recommended+{activity_clean}+{location_clean}"
                },
                {
                    "name": f"Best {activity} nearby",
                    "description": f"Local favorites near you",
                    "link": f"https://www.google.com/maps/search/best+{activity_clean}+near+{location_clean}"
                }
            ]
            
            return {
                'success': True,
                'venues': venues
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
    
    def _fallback_availability_parsing(self, text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Simple fallback availability parsing when OpenAI is unavailable.
        """
        import re
        from datetime import datetime, timedelta
        
        logger.info("Using fallback availability parsing")
        
        text_lower = text.lower()
        
        # Common day patterns
        days = {
            'monday': 1, 'tuesday': 2, 'wednesday': 3, 'thursday': 4,
            'friday': 5, 'saturday': 6, 'sunday': 0,
            'mon': 1, 'tue': 2, 'wed': 3, 'thu': 4, 'fri': 5, 'sat': 6, 'sun': 0
        }
        
        available_dates = []
        current_year = datetime.now().year
        
        # Try to parse "Monday after 2pm", "Monday 2-5pm", etc.
        for day_name, day_num in days.items():
            if day_name in text_lower:
                # Find next occurrence of this day
                today = datetime.now()
                days_ahead = (day_num - today.weekday()) % 7
                if days_ahead == 0:  # Today
                    days_ahead = 7  # Next week
                target_date = today + timedelta(days=days_ahead)
                
                # Look for time patterns
                time_patterns = [
                    r'after (\d{1,2})(?::(\d{2}))?\s*(am|pm)?',
                    r'from (\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*-\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?',
                    r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*-\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?'
                ]
                
                time_found = False
                for pattern in time_patterns:
                    matches = re.finditer(pattern, text_lower)
                    for match in matches:
                        groups = match.groups()
                        if 'after' in pattern:
                            # "after 2pm" - available from that time to end of day
                            hour = int(groups[0])
                            minute = int(groups[1]) if groups[1] else 0
                            am_pm = groups[2] or 'pm'
                            
                            if am_pm == 'pm' and hour < 12:
                                hour += 12
                            elif am_pm == 'am' and hour == 12:
                                hour = 0
                            
                            available_dates.append({
                                "date": target_date.strftime('%Y-%m-%d'),
                                "start_time": f"{hour:02d}:{minute:02d}",
                                "end_time": "23:59",
                                "all_day": False,
                                "preference": "available"
                            })
                            time_found = True
                        else:
                            # Range like "2-5pm" or "from 2pm-5pm"
                            start_hour = int(groups[0])
                            start_minute = int(groups[1]) if groups[1] else 0
                            start_am_pm = groups[2]
                            end_hour = int(groups[3]) if len(groups) > 3 and groups[3] else None
                            end_minute = int(groups[4]) if len(groups) > 4 and groups[4] else 0
                            end_am_pm = groups[5] if len(groups) > 5 else groups[2]
                            
                            if end_hour:
                                # Adjust hours for AM/PM
                                if start_am_pm == 'pm' and start_hour < 12:
                                    start_hour += 12
                                elif start_am_pm == 'am' and start_hour == 12:
                                    start_hour = 0
                                
                                if end_am_pm == 'pm' and end_hour < 12:
                                    end_hour += 12
                                elif end_am_pm == 'am' and end_hour == 12:
                                    end_hour = 0
                                
                                available_dates.append({
                                    "date": target_date.strftime('%Y-%m-%d'),
                                    "start_time": f"{start_hour:02d}:{start_minute:02d}",
                                    "end_time": f"{end_hour:02d}:{end_minute:02d}",
                                    "all_day": False,
                                    "preference": "available"
                                })
                                time_found = True
                
                # If day mentioned but no specific time, assume all day
                if not time_found and day_name in text_lower:
                    available_dates.append({
                        "date": target_date.strftime('%Y-%m-%d'),
                        "start_time": "09:00",
                        "end_time": "17:00",
                        "all_day": True,
                        "preference": "available"
                    })
        
        if available_dates:
            return {
                "available_dates": available_dates,
                "unavailable_dates": [],
                "notes": f"Parsed from: {text}",
                "confidence": "medium"
            }
        else:
            # If nothing parsed, return error
            return {
                "error": "Could not parse availability format",
                "confidence": "low"
            }


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


def is_broad_activity(activity: str) -> Dict[str, Any]:
    """
    Check if an activity description is too broad and provide suggestions.
    
    Args:
        activity: The activity description to check
        
    Returns:
        dict: Contains 'is_broad', 'suggestion', and 'matched_term'
    """
    activity_lower = activity.lower().strip()
    
    broad_terms = {
        'chinese food': 'Chinese restaurant',
        'chinese': 'Chinese restaurant', 
        'italian food': 'Italian restaurant',
        'italian': 'Italian restaurant',
        'thai food': 'Thai restaurant',
        'thai': 'Thai restaurant',
        'mexican food': 'Mexican restaurant',
        'mexican': 'Mexican restaurant',
        'japanese food': 'Japanese restaurant or sushi restaurant',
        'japanese': 'Japanese restaurant or sushi restaurant',
        'indian food': 'Indian restaurant',
        'indian': 'Indian restaurant',
        'food': 'specific restaurant type (e.g., "pizza place", "burger joint")',
        'dinner': 'specific restaurant type (e.g., "steakhouse", "seafood restaurant")',
        'lunch': 'specific restaurant type (e.g., "sandwich shop", "salad bar")',
        'drinks': 'specific bar type (e.g., "sports bar", "cocktail lounge")',
        'bar': 'specific bar type (e.g., "sports bar", "wine bar", "rooftop bar")',
        'eat': 'specific restaurant type (e.g., "pizza place", "burger joint")',
        'eating': 'specific restaurant type (e.g., "pizza place", "burger joint")', 
        'restaurant': 'specific restaurant type (e.g., "Italian restaurant", "pizza place")',
        'cuisine': 'specific restaurant type (e.g., "Thai restaurant", "burger joint")'
    }
    
    # Direct match first
    if activity_lower in broad_terms:
        return {
            'is_broad': True,
            'suggestion': broad_terms[activity_lower],
            'matched_term': activity_lower
        }
    
    # Check if activity contains broad terms (for short phrases)
    if len(activity_lower.split()) <= 2:
        for broad_term, suggestion in broad_terms.items():
            if broad_term in activity_lower:
                return {
                    'is_broad': True,
                    'suggestion': suggestion,
                    'matched_term': broad_term
                }
    
    return {
        'is_broad': False,
        'suggestion': None,
        'matched_term': None
    }


def suggest_venues(activity: str, location: str, requirements: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Convenience function for venue suggestions that accepts all activity types.
    
    Args:
        activity: The activity description (accepts broad terms like "chinese food")
        location: The location for the venue
        requirements: Optional list of additional requirements
        
    Returns:
        dict: Venue suggestions with AI interpreting broad terms intelligently
    """
    # Accept all activities and let AI interpret them intelligently
    # No more broad term rejection - the AI is smart enough to handle "chinese food" -> "Chinese restaurants"
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
