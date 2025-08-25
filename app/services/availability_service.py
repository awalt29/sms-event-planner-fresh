from typing import List, Dict
import logging
from app.models.availability import Availability
from datetime import datetime

logger = logging.getLogger(__name__)

class AvailabilityService:
    """Manages availability calculation and overlap detection"""
    
    def _format_time_12hour(self, time_str: str) -> str:
        """Convert 24-hour time string to 12-hour format with AM/PM"""
        try:
            from datetime import datetime
            # Parse the time string (assuming HH:MM format)
            time_obj = datetime.strptime(time_str, '%H:%M').time()
            # Format to 12-hour with AM/PM, remove leading zero and :00 for exact hours
            formatted = time_obj.strftime('%I:%M%p').lower()
            # Remove leading zero and simplify exact hours
            if formatted.startswith('0'):
                formatted = formatted[1:]
            if formatted.endswith(':00am'):
                formatted = formatted[:-5] + 'am'
            elif formatted.endswith(':00pm'):
                formatted = formatted[:-5] + 'pm'
            return formatted
        except:
            return time_str  # Return original if conversion fails
    
    def update_guest_availability(self, guest_id: int, event_id: int, availability_data: List[Dict]) -> bool:
        """Safely update guest availability, preventing duplicates"""
        try:
            # Clear existing availability records for this guest and event
            existing_records = Availability.query.filter_by(
                guest_id=guest_id,
                event_id=event_id
            ).all()
            
            if existing_records:
                logger.info(f"Clearing {len(existing_records)} existing availability records for guest {guest_id}")
                for record in existing_records:
                    record.delete()
            
            # Create new availability records
            created_count = 0
            for avail_data in availability_data:
                availability = Availability(
                    event_id=event_id,
                    guest_id=guest_id,
                    date=datetime.strptime(avail_data['date'], '%Y-%m-%d').date(),
                    start_time=datetime.strptime(avail_data['start_time'], '%H:%M').time(),
                    end_time=datetime.strptime(avail_data['end_time'], '%H:%M').time(),
                    all_day=avail_data.get('all_day', False)
                )
                availability.save()
                created_count += 1
                logger.info(f"Created availability: guest {guest_id}, date {avail_data['date']}, time {avail_data['start_time']}-{avail_data['end_time']}")
            
            logger.info(f"Successfully updated availability for guest {guest_id}: {created_count} records created")
            return True
            
        except Exception as e:
            logger.error(f"Error updating guest availability: {e}")
            return False
    
    def calculate_availability_overlaps(self, event_id: int, show_individual_availability: bool = False) -> List[Dict]:
        """Calculate optimal meeting times from guest availability"""
        try:
            # Get all availability records for this event with valid guests who have provided availability
            from app.models.guest import Guest
            availabilities = Availability.query.join(Guest).filter(
                Availability.event_id == event_id,
                Guest.availability_provided == True  # Only include guests who have actually responded
            ).all()
            
            if not availabilities:
                return []
            
            # Group by date and calculate overlaps
            date_overlaps = {}
            
            for availability in availabilities:
                # Skip availability records with missing guest data
                if not availability.guest:
                    logger.warning(f"Skipping availability {availability.id} - missing guest")
                    continue
                    
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
                    date_overlaps_list = self._calculate_time_overlap(date_data['guests'], show_individual_availability)
                    for overlap in date_overlaps_list:
                        overlap['date'] = date_data['date']
                        # If not already set by _calculate_time_overlap, deduplicate guest names
                        if 'available_guests' not in overlap:
                            unique_guest_names = list(set(g['guest_name'] for g in date_data['guests']))
                            overlap['available_guests'] = sorted(unique_guest_names)
                        if 'guest_count' not in overlap:
                            overlap['guest_count'] = len(overlap['available_guests'])
                        overlap_results.append(overlap)
            
            # Sort by guest count (descending) then by date
            overlap_results.sort(key=lambda x: (-x['guest_count'], x['date'] or ''))
            
            return overlap_results[:5]  # Top 5 options
            
        except Exception as e:
            logger.error(f"Error calculating overlaps: {e}")
            return []
    
    def _calculate_time_overlap(self, guest_availabilities: List[Dict], show_individual_availability: bool = False) -> List[Dict]:
        """Calculate time overlaps for a specific date based on business rules"""
        try:
            if not guest_availabilities:
                return []
            
            # For "view current overlaps", show individual availability when that's all we have
            # For final time selection, require at least 2 guests for true overlaps
            if len(guest_availabilities) < 2:
                if show_individual_availability:
                    # Show individual guest availability for status viewing
                    guest = guest_availabilities[0]
                    if guest['all_day']:
                        return [{
                            'start_time': '08:00',
                            'end_time': '23:59',
                            'all_day': True,
                            'available_guests': [guest['guest_name']],
                            'guest_count': 1
                        }]
                    else:
                        return [{
                            'start_time': guest['start_time'].strftime('%H:%M'),
                            'end_time': guest['end_time'].strftime('%H:%M'),
                            'all_day': False,
                            'available_guests': [guest['guest_name']],
                            'guest_count': 1
                        }]
                else:
                    # For time selection, require true overlaps (2+ guests)
                    return []
            
            overlaps = []
            
            # Handle all-day guests specially
            all_day_guests = [g for g in guest_availabilities if g['all_day']]
            timed_guests = [g for g in guest_availabilities if not g['all_day']]
            
            # Case 1: If all guests are all-day, create one full-day overlap
            if len(all_day_guests) >= 2 and len(timed_guests) == 0:
                return [{
                    'start_time': self._format_time_12hour('08:00'),
                    'end_time': self._format_time_12hour('23:59'), 
                    'all_day': True,
                    'available_guests': sorted([g['guest_name'] for g in all_day_guests]),
                    'guest_count': len(all_day_guests)
                }]
            
            # Case 2: Mixed all-day and timed guests, or all timed guests
            # Get all unique time points from timed guests
            time_points = set()
            for guest in timed_guests:
                if guest['start_time'] and guest['end_time']:
                    time_points.add(guest['start_time'])
                    time_points.add(guest['end_time'])
            
            # If we have all-day guests but no time points from timed guests, 
            # use reasonable default time range
            if all_day_guests and not time_points:
                from datetime import time as dt_time
                time_points.add(dt_time(8, 0))   # 8am
                time_points.add(dt_time(23, 59)) # 11:59pm
            
            time_points = sorted(time_points)
            
            # Find all possible overlapping windows (not just adjacent intervals)
            for i in range(len(time_points)):
                for j in range(i + 1, len(time_points)):
                    interval_start = time_points[i]
                    interval_end = time_points[j]
                    
                    # Count how many guests are available during this entire interval
                    available_guests = []
                    for guest in guest_availabilities:
                        if guest['all_day'] or (
                            guest['start_time'] <= interval_start and 
                            guest['end_time'] >= interval_end
                        ):
                            available_guests.append(guest['guest_name'])
                    
                    # Check if this interval meets our criteria
                    if len(available_guests) >= 2:  # At least 2 guests
                        # Calculate duration in hours
                        duration_seconds = (interval_end.hour * 3600 + interval_end.minute * 60) - \
                                         (interval_start.hour * 3600 + interval_start.minute * 60)
                        duration_hours = duration_seconds / 3600
                        
                        if duration_hours >= 2.0:  # At least 2 hours
                            overlaps.append({
                                'start_time': interval_start.strftime('%H:%M'),
                                'end_time': interval_end.strftime('%H:%M'),
                                'all_day': False,
                                'available_guests': sorted(list(set(available_guests))),  # Deduplicate and sort
                                'guest_count': len(set(available_guests)),
                                'duration_hours': duration_hours
                            })
            
            # Remove redundant overlaps - keep the longest duration for each guest set
            # Group by guest set, then pick the longest duration for each group
            guest_set_overlaps = {}
            for overlap in overlaps:
                guest_key = tuple(sorted(overlap['available_guests']))
                if guest_key not in guest_set_overlaps or overlap['duration_hours'] > guest_set_overlaps[guest_key]['duration_hours']:
                    guest_set_overlaps[guest_key] = overlap
            
            # Convert back to list and sort by guest count (descending) then by start time
            final_overlaps = list(guest_set_overlaps.values())
            final_overlaps.sort(key=lambda x: (-x['guest_count'], x['start_time']))
            
            # Remove the duration_hours field as it's just for internal processing
            for overlap in final_overlaps:
                overlap.pop('duration_hours', None)
            
            return final_overlaps
            
        except Exception as e:
            logger.error(f"Error calculating time overlap: {e}")
            return []
    
    def cleanup_orphaned_availability_records(self, event_id: int = None) -> int:
        """Clean up availability records that don't have associated guests"""
        try:
            from app.models.guest import Guest
            
            # Find availability records without valid guests
            if event_id:
                orphaned = Availability.query.filter(
                    Availability.event_id == event_id,
                    ~Availability.guest_id.in_(
                        Guest.query.with_entities(Guest.id).subquery()
                    )
                ).all()
            else:
                orphaned = Availability.query.filter(
                    ~Availability.guest_id.in_(
                        Guest.query.with_entities(Guest.id).subquery()
                    )
                ).all()
            
            count = len(orphaned)
            if count > 0:
                logger.info(f"Cleaning up {count} orphaned availability records")
                for record in orphaned:
                    record.delete()
            
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up orphaned availability records: {e}")
            return 0
