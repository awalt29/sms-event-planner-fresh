from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class VenueService:
    """Handles venue suggestions with AI and fallback options"""
    
    def __init__(self):
        from app.services.ai_processing_service import AIProcessingService
        self.ai_service = AIProcessingService()
    
    def get_venue_suggestions(self, activity: str, location: str, exclude_previous: bool = False, previous_venues: List[Dict] = None) -> List[Dict]:
        """Generate venue suggestions with Google Maps integration"""
        try:
            # Convert food terms intelligently
            processed_activity = self._convert_food_terms(activity)
            
            # Try AI-powered suggestions first
            ai_result = self._get_ai_venue_suggestions(
                processed_activity, 
                location, 
                exclude_previous=exclude_previous, 
                previous_venues=previous_venues
            )
            
            if ai_result.get('success') and ai_result.get('venues') and len(ai_result['venues']) > 0:
                return ai_result['venues']
            
            # If AI found no venues, check if we have curated suggestions for this activity
            processed_activity_lower = processed_activity.lower()
            curated_venues = self._get_curated_venue_suggestions(processed_activity, location)
            
            # Check if the curated venues are actually for the requested activity
            # If not, return an empty result with a helpful message
            if (processed_activity_lower not in ['coffee', 'chinese', 'italian', 'rooftop', 'bar', 'dinner', 'drinks'] and 
                not any(keyword in processed_activity_lower for keyword in ['food', 'restaurant', 'eat', 'drink'])):
                return []
            
            # Fallback to curated suggestions for food/drink activities
            return curated_venues
            
        except Exception as e:
            logger.error(f"Venue suggestion error: {e}")
            return self._get_curated_venue_suggestions(activity, location)
    
    def _convert_food_terms(self, activity: str) -> str:
        """Convert food terms to restaurant types for better AI understanding"""
        food_conversions = {
            'chinese food': 'Chinese restaurants',
            'italian food': 'Italian restaurants',
            'mexican food': 'Mexican restaurants',
            'pizza': 'pizza restaurants',
            'sushi': 'sushi restaurants',
            'thai food': 'Thai restaurants',
            'indian food': 'Indian restaurants',
            'japanese food': 'Japanese restaurants',
            'korean food': 'Korean restaurants',
            'vietnamese food': 'Vietnamese restaurants'
        }
        
        activity_lower = activity.lower().strip()
        return food_conversions.get(activity_lower, activity)
    
    def _get_ai_venue_suggestions(self, activity: str, location: str, exclude_previous: bool = False, previous_venues: List[Dict] = None, requirements: List[str] = None) -> Dict:
        """Get AI-powered venue suggestions"""
        try:
            if not self.ai_service.api_key:
                return {'success': False, 'error': 'AI service not available'}
                
            req_text = f" with {', '.join(requirements)}" if requirements else ""
            
            # Add exclusion text if we have previous venues to exclude
            exclude_text = ""
            if exclude_previous and previous_venues:
                venue_names = [venue.get('name', '') for venue in previous_venues if venue.get('name')]
                if venue_names:
                    exclude_text = f"\n\n🚫 CRITICAL EXCLUSION REQUIREMENT: You MUST NOT suggest any of these previously suggested venues: {', '.join(venue_names)}\n🚫 These venues are FORBIDDEN and must be completely avoided in your suggestions."
            
            prompt = f"""
            You are a local venue expert. Suggest 3 real, specific venues for "{activity}" in {location}{req_text}.{exclude_text}
            
            CRITICAL LOCATION REQUIREMENT: Prioritize venues located specifically in {location}. If no venues exist in {location}, you may suggest venues in nearby areas but clearly indicate their actual location.
            
            CRITICAL: Find venues that are SPECIFICALLY KNOWN FOR and SPECIALIZE IN "{activity}", not just places that might have it as a side feature.
            
            🔄 CRITICAL UNIQUENESS REQUIREMENT: Every venue suggestion must be completely NEW and DIFFERENT from any previously suggested venues. Never repeat venues from earlier suggestions.
            
            For "{activity}" venues, prioritize:
            - Places that are famous/known for this specific activity AND located in or near {location}
            - Venues where this activity is a main attraction, not just available
            - Establishments that advertise or are reviewed specifically for this activity
            - Prefer venues in {location}, but include nearby venues if {location} has none
            
            For each venue, provide:
            1. Real venue name (not generic names) with actual location if different from {location}
            2. Brief description (MAX 15 words) highlighting their specialization in "{activity}"
            3. ALWAYS use Google Maps search format: https://www.google.com/maps/search/?api=1&query=VENUE_NAME+ACTUAL_LOCATION
            
            CRITICAL LINK FORMAT RULES:
            - ALWAYS use Google Maps search format for consistency
            - Replace spaces with + in venue names and locations
            - Format: https://www.google.com/maps/search/?api=1&query=VenueName+ActualLocation
            - Do NOT use direct website URLs - always use Google Maps format
            - Example: "Joe's Pizza" in "Brooklyn" becomes https://www.google.com/maps/search/?api=1&query=Joe's+Pizza+Brooklyn
            
            CRITICAL: 
            - Keep descriptions to 15 words or less. Be concise and punchy.
            - If a venue is not in {location}, mention its actual neighborhood/area in the description
            - ALWAYS suggest NEW venues that are different from any previously suggested ones
            - Focus on venues that are actually known for "{activity}", not just bars/restaurants that happen to have it
            - If you cannot find any venues for "{activity}" in or near {location}, return an empty venues array
            
            Prioritize popular, well-known venues that actually exist, preferably in {location} but nearby if necessary.
            
            Return JSON with:
            {{
                "success": true,
                "venues": [
                    {{
                        "name": "Specific Real Venue Name",
                        "description": "Concise description in 15 words or less",
                        "link": "https://www.google.com/maps/search/?api=1&query=VenueName+Location"
                    }}
                ]
            }}
            
            Examples of correct link formatting:
            - "Xi'an Famous Foods" → "https://www.google.com/maps/search/?api=1&query=Xi'an+Famous+Foods+Williamsburg"
            - "1 or 8" → "https://www.google.com/maps/search/?api=1&query=1+or+8+Williamsburg"
            - "Bozu" → "https://www.google.com/maps/search/?api=1&query=Bozu+Williamsburg"
            """
            
            response = self.ai_service.make_completion(prompt, max_tokens=500)
            
            if response:
                import json
                try:
                    # Clean up response - remove markdown code blocks if present
                    cleaned_response = response.strip()
                    if cleaned_response.startswith('```json'):
                        cleaned_response = cleaned_response[7:]  # Remove ```json
                    if cleaned_response.endswith('```'):
                        cleaned_response = cleaned_response[:-3]  # Remove ```
                    cleaned_response = cleaned_response.strip()
                    
                    # Find the JSON part - look for { and stop at the first complete JSON object
                    start_idx = cleaned_response.find('{')
                    if start_idx != -1:
                        # Count braces to find the end of the JSON
                        brace_count = 0
                        end_idx = start_idx
                        for i, char in enumerate(cleaned_response[start_idx:], start_idx):
                            if char == '{':
                                brace_count += 1
                            elif char == '}':
                                brace_count -= 1
                                if brace_count == 0:
                                    end_idx = i + 1
                                    break
                        
                        json_only = cleaned_response[start_idx:end_idx]
                        return json.loads(json_only)
                    else:
                        return json.loads(cleaned_response)
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse AI venue response as JSON: {e}")
                    logger.error(f"Raw response: {response}")
                    return {'success': False, 'error': 'Invalid JSON response from AI'}
            else:
                logger.warning("AI service returned empty response for venue suggestions")
                return {'success': False, 'error': 'AI completion failed'}
            
        except Exception as e:
            logger.error(f"AI venue suggestion error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_curated_venue_suggestions(self, activity: str, location: str) -> List[Dict]:
        """Fallback curated venue suggestions"""
        # Curated suggestions based on activity type
        curated_venues = {
            'coffee': [
                {'name': 'Blue Bottle Coffee', 'description': 'Hip artisanal coffee shop', 'link': 'https://bluebottlecoffee.com/'},
                {'name': 'Stumptown Coffee', 'description': 'Portland-based specialty coffee', 'link': 'https://www.stumptowncoffee.com/'},
                {'name': 'Local Coffee House', 'description': 'Neighborhood coffee spot', 'link': None}
            ],
            'chinese': [
                {'name': 'Nom Wah Tea Parlor', 'description': 'Traditional dim sum', 'link': 'https://nomwah.com/'},
                {'name': "Xi'an Famous Foods", 'description': 'Hand-pulled noodles and spicy dishes', 'link': 'https://www.xianfoods.com/'},
                {'name': 'Golden Dragon', 'description': 'Authentic Chinese dishes', 'link': None}
            ],
            'italian': [
                {'name': 'Carbone', 'description': 'Upscale Italian-American', 'link': 'https://carbonenewyork.com/'},
                {'name': 'Via Carota', 'description': 'Cozy Italian bistro', 'link': None},
                {'name': 'Local Italian Kitchen', 'description': 'Neighborhood Italian spot', 'link': None}
            ],
            'rooftop': [
                {'name': 'Westlight', 'description': 'Stunning skyline views from William Vale Hotel', 'link': 'https://www.westlightnyc.com/'},
                {'name': '1 Rooftop', 'description': 'Chic rooftop bar with Manhattan views', 'link': 'https://www.1hotels.com/brooklyn-bridge/dining/1-rooftop'},
                {'name': 'Berry Park', 'description': 'Massive rooftop with outdoor games', 'link': 'https://berrypark.com/'},
                {'name': 'Elsewhere Rooftop', 'description': 'Multi-level rooftop with city views', 'link': 'https://elsewherebrooklyn.com/'}
            ],
            'bar': [
                {'name': 'Dead Rabbit', 'description': 'Award-winning cocktail bar', 'link': 'https://deadrabbitnyc.com/'},
                {'name': 'Craft Cocktail Lounge', 'description': 'Artisan cocktails', 'link': None},
                {'name': 'Neighborhood Pub', 'description': 'Friendly local hangout', 'link': None}
            ],
            'dinner': [
                {'name': 'The Local Bistro', 'description': 'Cozy neighborhood dining', 'link': None},
                {'name': 'Upscale Dining Room', 'description': 'Fine dining experience', 'link': None},
                {'name': 'Casual Family Restaurant', 'description': 'Relaxed atmosphere', 'link': None}
            ],
            'drinks': [
                {'name': 'Rooftop Bar', 'description': 'Great city views', 'link': None},
                {'name': 'Wine Bar', 'description': 'Curated wine selection', 'link': None},
                {'name': 'Craft Beer Hall', 'description': 'Local brewery taproom', 'link': None}
            ]
        }
        
        # Determine venue type from activity
        activity_lower = activity.lower()
        venue_type = 'coffee'  # default
        
        # Check for rooftop specifically
        if 'rooftop' in activity_lower:
            venue_type = 'rooftop'
        else:
            for key in curated_venues.keys():
                if key in activity_lower:
                    venue_type = key
                    break
        
        venues = curated_venues.get(venue_type, curated_venues['coffee'])
        
        # Add proper Google Maps links for venues without real websites
        for venue in venues:
            if not venue.get('link'):
                # Use proper Google Maps search API format with URL encoding
                import urllib.parse
                search_query = f"{venue['name']} {location}"
                encoded_query = urllib.parse.quote_plus(search_query)
                venue['link'] = f"https://www.google.com/maps/search/?api=1&query={encoded_query}"
        
        return venues
