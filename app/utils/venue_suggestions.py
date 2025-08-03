"""
New AI-powered venue suggestion system for the event planner.
Clean, simple, and reliable implementation.
"""

from openai import OpenAI
from flask import current_app
import json
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def suggest_venues(activity: str, location: str, requirements: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    AI-powered venue suggestions with intelligent activity conversion.
    
    Args:
        activity: Activity description (e.g., "chinese food", "italian restaurant")
        location: Location for the venue (e.g., "Brooklyn", "Manhattan")
        requirements: Optional additional requirements
        
    Returns:
        dict: Always successful venue suggestions with fallback system
    """
    try:
        logger.info(f"Suggesting venues for '{activity}' in '{location}'")
        
        # Smart conversion: Handle food terms intelligently
        processed_activity = convert_food_terms_to_restaurants(activity)
        if processed_activity != activity:
            logger.info(f"Converted '{activity}' -> '{processed_activity}'")
        
        # Try AI first, fallback to curated suggestions
        ai_result = try_ai_venue_suggestions(processed_activity, location, requirements)
        if ai_result['success']:
            return ai_result
        
        # AI failed, use curated fallback
        logger.info("AI failed, using curated venue suggestions")
        return get_curated_venue_suggestions(processed_activity, location)
        
    except Exception as e:
        logger.error(f"Error in suggest_venues: {e}")
        return get_curated_venue_suggestions(activity, location)


def convert_food_terms_to_restaurants(activity: str) -> str:
    """Convert food terms to restaurant terms for better AI understanding."""
    activity_lower = activity.lower().strip()
    
    # Food term conversions
    food_conversions = {
        'chinese food': 'Chinese restaurants',
        'italian food': 'Italian restaurants', 
        'thai food': 'Thai restaurants',
        'mexican food': 'Mexican restaurants',
        'indian food': 'Indian restaurants',
        'japanese food': 'Japanese restaurants',
        'korean food': 'Korean restaurants',
        'vietnamese food': 'Vietnamese restaurants',
        'french food': 'French restaurants',
        'pizza': 'pizza restaurants',
        'sushi': 'sushi restaurants',
        'seafood': 'seafood restaurants'
    }
    
    for food_term, restaurant_term in food_conversions.items():
        if food_term in activity_lower:
            return restaurant_term
    
    return activity


def try_ai_venue_suggestions(activity: str, location: str, requirements: Optional[List[str]] = None) -> Dict[str, Any]:
    """Try to get venue suggestions from OpenAI."""
    try:
        # Get API key
        api_key = current_app.config.get('OPENAI_API_KEY')
        if not api_key:
            logger.error("No OpenAI API key found")
            return {'success': False, 'error': 'No API key'}
        
        # Create client
        client = OpenAI(api_key=api_key)
        
        # Create simple, clear prompt
        prompt = f"""Please suggest exactly 3 popular {activity} in {location}.

Return only this JSON format:
{{
  "venues": [
    {{"name": "Real Venue Name", "description": "Brief description"}},
    {{"name": "Real Venue Name", "description": "Brief description"}},
    {{"name": "Real Venue Name", "description": "Brief description"}}
  ]
}}

Requirements:
- Real, existing venues only
- Popular and well-reviewed
- Brief descriptions (under 10 words)
- No explanations, just the JSON"""

        if requirements:
            prompt += f"\nAdditional requirements: {', '.join(requirements)}"
        
        # Call OpenAI with timeout
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You suggest real venues. Always return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300,
            timeout=20  # Shorter timeout
        )
        
        content = response.choices[0].message.content.strip()
        logger.info(f"OpenAI response: {content[:100]}...")
        
        # Parse JSON
        venue_data = json.loads(content)
        venues = venue_data.get('venues', [])
        
        # Format venues with Google Maps links
        formatted_venues = []
        for venue in venues[:3]:
            if venue.get('name'):
                formatted_venue = {
                    'name': venue['name'],
                    'description': venue.get('description', ''),
                    'link': create_google_maps_link(venue['name'], location)
                }
                formatted_venues.append(formatted_venue)
        
        if formatted_venues:
            logger.info(f"AI successfully generated {len(formatted_venues)} venues")
            return {
                'success': True,
                'venues': formatted_venues,
                'method': 'ai'
            }
        else:
            logger.warning("No valid venues from AI")
            return {'success': False, 'error': 'No valid venues'}
            
    except Exception as e:
        logger.error(f"AI venue suggestion failed: {e}")
        return {'success': False, 'error': str(e)}


def get_curated_venue_suggestions(activity: str, location: str) -> Dict[str, Any]:
    """Get curated venue suggestions when AI fails."""
    try:
        logger.info(f"Using curated suggestions for '{activity}' in '{location}'")
        
        # Normalize inputs
        activity_key = normalize_activity_for_curation(activity)
        location_key = normalize_location_for_curation(location)
        
        # Get venues from curated database
        venues = get_venues_from_database(activity_key, location_key)
        
        # Format with Google Maps links
        formatted_venues = []
        for venue in venues[:3]:
            formatted_venue = {
                'name': venue['name'],
                'description': venue['description'],
                'link': create_google_maps_link(venue['name'], location)
            }
            formatted_venues.append(formatted_venue)
        
        logger.info(f"Curated system provided {len(formatted_venues)} venues")
        return {
            'success': True,
            'venues': formatted_venues,
            'method': 'curated'
        }
        
    except Exception as e:
        logger.error(f"Curated venue suggestion failed: {e}")
        # Ultimate fallback
        return {
            'success': True,
            'venues': [
                {
                    'name': f"Search {activity} in {location}",
                    'description': f"Find {activity} venues nearby",
                    'link': create_google_maps_link(activity, location)
                }
            ],
            'method': 'emergency_fallback'
        }


def normalize_activity_for_curation(activity: str) -> str:
    """Normalize activity for curated database lookup."""
    activity_lower = activity.lower().strip()
    
    if any(term in activity_lower for term in ['chinese', 'china']):
        return 'chinese'
    elif any(term in activity_lower for term in ['italian', 'italy', 'pizza']):
        return 'italian'
    elif any(term in activity_lower for term in ['coffee', 'cafe']):
        return 'coffee'
    elif any(term in activity_lower for term in ['bar', 'drink', 'cocktail']):
        return 'bar'
    elif any(term in activity_lower for term in ['brunch', 'breakfast']):
        return 'brunch'
    else:
        return 'general'


def normalize_location_for_curation(location: str) -> str:
    """Normalize location for curated database lookup."""
    location_lower = location.lower().strip()
    
    if any(term in location_lower for term in ['brooklyn', 'williamsburg', 'dumbo']):
        return 'brooklyn'
    elif any(term in location_lower for term in ['manhattan', 'nyc', 'new york']):
        return 'manhattan'
    elif 'queens' in location_lower:
        return 'queens'
    else:
        return 'general'


def get_venues_from_database(activity_key: str, location_key: str) -> List[Dict[str, str]]:
    """Get venues from curated database."""
    
    # Curated venue database
    venues_db = {
        'chinese': {
            'brooklyn': [
                {"name": "Nom Wah Tea Parlor", "description": "Historic dim sum restaurant"},
                {"name": "Jade Asian Restaurant", "description": "Traditional Cantonese cuisine"},
                {"name": "Golden Dragon", "description": "Family-style Chinese dining"}
            ],
            'manhattan': [
                {"name": "Joe's Shanghai", "description": "Famous soup dumplings"},
                {"name": "Xi'an Famous Foods", "description": "Hand-pulled noodles"},
                {"name": "Hakkasan", "description": "Upscale modern Chinese"}
            ],
            'general': [
                {"name": "Local Chinese Restaurant", "description": "Neighborhood Chinese food"},
                {"name": "Golden Palace", "description": "Traditional Chinese cuisine"},
                {"name": "China Garden", "description": "Family-style Chinese dining"}
            ]
        },
        'italian': {
            'brooklyn': [
                {"name": "L'industrie Pizzeria", "description": "Popular pizza spot"},
                {"name": "Lucali", "description": "Thin crust pizza"},
                {"name": "Juliana's", "description": "Coal oven pizza"}
            ],
            'manhattan': [
                {"name": "Carbone", "description": "Upscale Italian-American"},
                {"name": "Via Carota", "description": "Cozy village Italian"},
                {"name": "Don Angie", "description": "Modern Italian"}
            ],
            'general': [
                {"name": "Tony's Italian", "description": "Classic Italian dishes"},
                {"name": "Mama Mia Pizzeria", "description": "Wood-fired pizza"},
                {"name": "Little Italy Restaurant", "description": "Traditional Italian"}
            ]
        },
        'coffee': {
            'brooklyn': [
                {"name": "Blue Bottle Coffee", "description": "Specialty coffee roaster"},
                {"name": "Toby's Estate Coffee", "description": "Australian-style coffee"},
                {"name": "Ninth Street Espresso", "description": "Local coffee favorite"}
            ],
            'manhattan': [
                {"name": "Stumptown Coffee", "description": "Portland-based roaster"},
                {"name": "Irving Farm Coffee", "description": "NYC coffee institution"},
                {"name": "La Colombe", "description": "Philly-based coffee"}
            ],
            'general': [
                {"name": "Local Coffee House", "description": "Neighborhood coffee shop"},
                {"name": "The Daily Grind", "description": "Cozy coffee spot"},
                {"name": "Brew & Bean", "description": "Artisan coffee"}
            ]
        },
        'bar': {
            'brooklyn': [
                {"name": "House of Yes", "description": "Creative cocktails & performances"},
                {"name": "Clover Club", "description": "Classic cocktail bar"},
                {"name": "Weather Up", "description": "Neighborhood cocktail spot"}
            ],
            'manhattan': [
                {"name": "Please Don't Tell (PDT)", "description": "Hidden speakeasy"},
                {"name": "Death & Co", "description": "Craft cocktail pioneer"},
                {"name": "Employees Only", "description": "Classic cocktail bar"}
            ],
            'general': [
                {"name": "Local Sports Bar", "description": "Neighborhood bar with drinks"},
                {"name": "The Tap House", "description": "Craft beer & cocktails"},
                {"name": "Happy Hour Lounge", "description": "Casual drinks spot"}
            ]
        },
        'brunch': {
            'brooklyn': [
                {"name": "Clinton Street Baking Co.", "description": "Famous for pancakes"},
                {"name": "Egg", "description": "Southern-style brunch"},
                {"name": "Five Leaves", "description": "Australian-inspired brunch"}
            ],
            'manhattan': [
                {"name": "Balthazar", "description": "French bistro brunch"},
                {"name": "Sarabeth's", "description": "Classic NYC brunch"},
                {"name": "Jacob's Pickles", "description": "Southern comfort brunch"}
            ],
            'general': [
                {"name": "Sunday Brunch Cafe", "description": "Weekend brunch spot"},
                {"name": "The Breakfast Club", "description": "All-day breakfast"},
                {"name": "Mimosa & More", "description": "Boozy brunch spot"}
            ]
        }
    }
    
    # Get venues for the activity and location
    if activity_key in venues_db:
        if location_key in venues_db[activity_key]:
            return venues_db[activity_key][location_key]
        else:
            return venues_db[activity_key]['general']
    else:
        # Generic venues for unknown activities
        return [
            {"name": "Popular Local Venue", "description": f"Great place for {activity_key}"},
            {"name": "Neighborhood Favorite", "description": f"Well-reviewed {activity_key} spot"},
            {"name": "Local Hotspot", "description": f"Trending {activity_key} venue"}
        ]


def create_google_maps_link(venue_name: str, location: str) -> str:
    """Create a Google Maps search link."""
    search_query = f"{venue_name} {location}".replace(' ', '+')
    return f"https://www.google.com/maps/search/{search_query}"
