from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class VenueService:
    """Handles venue suggestions with AI and fallback options"""
    
    def __init__(self):
        from app.services.ai_processing_service import AIProcessingService
        self.ai_service = AIProcessingService()
    
    def get_venue_suggestions(self, activity: str, location: str, exclude_previous: bool = False) -> List[Dict]:
        """Generate venue suggestions with Google Maps integration"""
        try:
            # Convert food terms intelligently
            processed_activity = self._convert_food_terms(activity)
            
            # Try AI-powered suggestions first
            ai_result = self._get_ai_venue_suggestions(processed_activity, location)
            
            if ai_result.get('success') and ai_result.get('venues'):
                return ai_result['venues']
            
            # Fallback to curated suggestions
            return self._get_curated_venue_suggestions(processed_activity, location)
            
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
    
    def _get_ai_venue_suggestions(self, activity: str, location: str, requirements: List[str] = None) -> Dict:
        """Get AI-powered venue suggestions"""
        try:
            if not self.ai_service.client:
                return {'success': False, 'error': 'AI service not available'}
                
            req_text = f" with {', '.join(requirements)}" if requirements else ""
            
            prompt = f"""
            Suggest 3 specific venue names for "{activity}" in {location}{req_text}.
            
            Return JSON with:
            {{
                "success": true,
                "venues": [
                    {{
                        "name": "Specific Venue Name",
                        "description": "Brief description",
                        "link": "https://www.google.com/maps/search/VenueName+{location}+{activity}"
                    }}
                ]
            }}
            """
            
            response = self.ai_service.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                timeout=20
            )
            
            import json
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"AI venue suggestion error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_curated_venue_suggestions(self, activity: str, location: str) -> List[Dict]:
        """Fallback curated venue suggestions"""
        # Curated suggestions based on activity type
        curated_venues = {
            'coffee': [
                {'name': 'Starbucks', 'description': 'Global coffee chain'},
                {'name': 'Blue Bottle Coffee', 'description': 'Hip artisanal coffee shop'},
                {'name': 'Local Coffee House', 'description': 'Neighborhood coffee spot'}
            ],
            'chinese': [
                {'name': 'Nom Wah Tea Parlor', 'description': 'Traditional dim sum'},
                {'name': 'Jade Asian Restaurant', 'description': 'Modern Chinese cuisine'},
                {'name': 'Golden Dragon', 'description': 'Authentic Chinese dishes'}
            ],
            'italian': [
                {'name': 'Carbone', 'description': 'Upscale Italian-American'},
                {'name': 'Via Carota', 'description': 'Cozy Italian bistro'},
                {'name': 'Local Italian Kitchen', 'description': 'Neighborhood Italian spot'}
            ],
            'bar': [
                {'name': 'Local Sports Bar', 'description': 'Casual drinks & games'},
                {'name': 'Craft Cocktail Lounge', 'description': 'Artisan cocktails'},
                {'name': 'Neighborhood Pub', 'description': 'Friendly local hangout'}
            ],
            'dinner': [
                {'name': 'The Local Bistro', 'description': 'Cozy neighborhood dining'},
                {'name': 'Upscale Dining Room', 'description': 'Fine dining experience'},
                {'name': 'Casual Family Restaurant', 'description': 'Relaxed atmosphere'}
            ],
            'drinks': [
                {'name': 'Rooftop Bar', 'description': 'Great city views'},
                {'name': 'Wine Bar', 'description': 'Curated wine selection'},
                {'name': 'Craft Beer Hall', 'description': 'Local brewery taproom'}
            ]
        }
        
        # Determine venue type from activity
        activity_lower = activity.lower()
        venue_type = 'coffee'  # default
        
        for key in curated_venues.keys():
            if key in activity_lower:
                venue_type = key
                break
        
        venues = curated_venues.get(venue_type, curated_venues['coffee'])
        
        # Add Google Maps links
        for venue in venues:
            search_terms = f"{venue['name']}+{location}+{activity}".replace(' ', '+')
            venue['link'] = f"https://www.google.com/maps/search/{search_terms}"
        
        return venues
