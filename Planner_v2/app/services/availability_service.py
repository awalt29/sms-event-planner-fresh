from typing import List, Dict
import logging
from app.models.availability import Availability

logger = logging.getLogger(__name__)

class AvailabilityService:
    """Manages availability calculation and overlap detection"""
    
    def calculate_availability_overlaps(self, event_id: int) -> List[Dict]:
        """Calculate optimal meeting times from guest availability"""
        try:
            # Get all availability records for this event
            availabilities = Availability.query.filter_by(event_id=event_id).all()
            
            if not availabilities:
                return []
            
            # Group by date and calculate overlaps
            date_overlaps = {}
            
            for availability in availabilities:
                date_key = availability.date.isoformat() if availability.date else 'unknown'
                
                if date_key not in date_overlaps:
                    date_overlaps[date_key] = {
                        'date': availability.date,
                        'guests': [],
                        'time_slots': []
                    }
                
                guest_info = {
                    'guest_id': availability.guest_id,
                    'guest_name': availability.guest.name,
                    'start_time': availability.start_time,
                    'end_time': availability.end_time,
                    'all_day': availability.all_day
                }
                
                date_overlaps[date_key]['guests'].append(guest_info)
            
            # Calculate actual overlaps
            overlap_results = []
            
            for date_key, date_data in date_overlaps.items():
                if len(date_data['guests']) >= 1:  # At least one guest available
                    overlap = self._calculate_time_overlap(date_data['guests'])
                    if overlap:
                        overlap['date'] = date_data['date']
                        overlap['guest_count'] = len(date_data['guests'])
                        overlap['available_guests'] = [g['guest_name'] for g in date_data['guests']]
                        overlap_results.append(overlap)
            
            # Sort by guest count (descending) then by date
            overlap_results.sort(key=lambda x: (-x['guest_count'], x['date'] or ''))
            
            return overlap_results[:5]  # Top 5 options
            
        except Exception as e:
            logger.error(f"Error calculating overlaps: {e}")
            return []
    
    def _calculate_time_overlap(self, guest_availabilities: List[Dict]) -> Dict:
        """Calculate time overlap for a specific date"""
        try:
            # Handle all-day availability
            has_all_day = any(g['all_day'] for g in guest_availabilities)
            
            if has_all_day:
                return {
                    'start_time': '00:00',
                    'end_time': '23:59',
                    'all_day': True
                }
            
            # Calculate time overlap
            earliest_start = None
            latest_end = None
            
            for guest in guest_availabilities:
                if guest['start_time'] and guest['end_time']:
                    if earliest_start is None or guest['start_time'] < earliest_start:
                        earliest_start = guest['start_time']
                    if latest_end is None or guest['end_time'] > latest_end:
                        latest_end = guest['end_time']
            
            if earliest_start and latest_end:
                return {
                    'start_time': earliest_start.strftime('%H:%M'),
                    'end_time': latest_end.strftime('%H:%M'),
                    'all_day': False
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error calculating time overlap: {e}")
            return None
