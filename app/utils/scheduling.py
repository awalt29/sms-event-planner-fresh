from datetime import datetime, timedelta
import re
from typing import List, Tuple, Dict, Any
from app.models import Availability, Event, Guest


def calculate_availability_overlaps(event_id: int) -> List[Dict[str, Any]]:
    """
    Calculate availability overlaps for an event and return sorted timeslots.
    
    Args:
        event_id: The ID of the event to calculate overlaps for
        
    Returns:
        List of overlapping timeslots sorted by guest count (descending)
    """
    from app.models import db
    
    # Get the event and all guest availabilities
    event = Event.query.get(event_id)
    if not event:
        return []
    
    # Get all availability records for this event
    availabilities = Availability.query.filter_by(event_id=event_id).all()
    if not availabilities:
        return []
    
    # Group availabilities by date
    date_groups = {}
    for avail in availabilities:
        if avail.date:
            date_key = avail.date.isoformat()
            if date_key not in date_groups:
                date_groups[date_key] = []
            date_groups[date_key].append(avail)
    
    overlaps = []
    
    for date_str, date_availabilities in date_groups.items():
        if len(date_availabilities) < 1:  # At least one person must be available
            continue
            
        date_obj = datetime.fromisoformat(date_str).date()
        
        # Handle all-day availability
        all_day_guests = [avail for avail in date_availabilities if avail.all_day]
        if all_day_guests:
            guest_names = [avail.guest.name or f"Guest {avail.guest.id}" for avail in all_day_guests]
            overlaps.append({
                'date': date_obj,
                'start_time': None,
                'end_time': None,
                'all_day': True,
                'guest_count': len(all_day_guests),
                'available_guests': guest_names,
                'confidence': 'high'
            })
        
        # Handle timed availability
        timed_guests = [avail for avail in date_availabilities if not avail.all_day and avail.start_time]
        if len(timed_guests) >= 1:
            # Find overlapping time windows
            time_overlaps = find_time_overlaps(timed_guests)
            for overlap in time_overlaps:
                overlaps.append({
                    'date': date_obj,
                    'start_time': overlap['start_time'],
                    'end_time': overlap['end_time'],
                    'all_day': False,
                    'guest_count': overlap['guest_count'],
                    'available_guests': overlap['available_guests'],
                    'confidence': overlap['confidence']
                })
    
    # Sort by guest count (descending), then by confidence
    overlaps.sort(key=lambda x: (x['guest_count'], x['confidence'] == 'high'), reverse=True)
    
    return overlaps


def find_time_overlaps(timed_availabilities: List[Availability]) -> List[Dict[str, Any]]:
    """
    Find overlapping time windows from timed availability records.
    For single guest, return their availability as valid timeslots.
    """
    if not timed_availabilities:
        return []
    
    # Convert to time intervals for easier processing
    intervals = []
    for avail in timed_availabilities:
        start_time = avail.start_time
        end_time = avail.end_time or datetime.strptime("23:59", "%H:%M").time()  # Default to end of day
        
        intervals.append({
            'start': start_time,
            'end': end_time,
            'guest': avail.guest,
            'availability': avail
        })
    
    # Sort intervals by start time
    intervals.sort(key=lambda x: x['start'])
    
    overlaps = []
    
    # Special case: if only one guest, return their availability as valid timeslots
    if len(intervals) == 1:
        interval = intervals[0]
        guest_name = interval['guest'].name or f"Guest {interval['guest'].id}"
        
        # Calculate duration
        start_dt = datetime.combine(datetime.today(), interval['start'])
        end_dt = datetime.combine(datetime.today(), interval['end'])
        duration = end_dt - start_dt
        
        # Only include if at least 1 hour duration
        if duration >= timedelta(hours=1):
            overlaps.append({
                'start_time': interval['start'].strftime('%H:%M'),
                'end_time': interval['end'].strftime('%H:%M'),
                'guest_count': 1,
                'available_guests': [guest_name],
                'confidence': 'high' if duration >= timedelta(hours=2) else 'medium'
            })
        
        return overlaps
    
    # Find all possible overlapping windows for multiple guests
    for i in range(len(intervals)):
        for j in range(i + 1, len(intervals)):
            interval1 = intervals[i]
            interval2 = intervals[j]
            
            # Check if intervals overlap
            overlap_start = max(interval1['start'], interval2['start'])
            overlap_end = min(interval1['end'], interval2['end'])
            
            if overlap_start < overlap_end:
                # Calculate duration (at least 1 hour overlap to be meaningful)
                start_dt = datetime.combine(datetime.today(), overlap_start)
                end_dt = datetime.combine(datetime.today(), overlap_end)
                duration = end_dt - start_dt
                
                if duration >= timedelta(hours=1):
                    guest_names = [
                        interval1['guest'].name or f"Guest {interval1['guest'].id}",
                        interval2['guest'].name or f"Guest {interval2['guest'].id}"
                    ]
                    
                    overlaps.append({
                        'start_time': overlap_start.strftime('%H:%M'),
                        'end_time': overlap_end.strftime('%H:%M'),
                        'guest_count': 2,
                        'available_guests': guest_names,
                        'confidence': 'high' if duration >= timedelta(hours=2) else 'medium'
                    })
    
    # Remove duplicate overlaps and merge similar ones
    unique_overlaps = []
    for overlap in overlaps:
        # Check if we already have a similar overlap
        similar_found = False
        for existing in unique_overlaps:
            if (existing['start_time'] == overlap['start_time'] and 
                existing['end_time'] == overlap['end_time']):
                # Merge guest lists
                all_guests = list(set(existing['available_guests'] + overlap['available_guests']))
                existing['available_guests'] = all_guests
                existing['guest_count'] = len(all_guests)
                similar_found = True
                break
        
        if not similar_found:
            unique_overlaps.append(overlap)
    
    return unique_overlaps


def find_overlapping_availability(availabilities: List[Availability]) -> List[Dict[str, Any]]:
    """
    Find overlapping time slots from multiple guest availabilities.
    
    Args:
        availabilities: List of Availability objects
        
    Returns:
        list: List of overlapping time slots with details
    """
    if not availabilities:
        return []
    
    # Group availabilities by date
    date_groups = {}
    for avail in availabilities:
        date_key = avail.date.isoformat()
        if date_key not in date_groups:
            date_groups[date_key] = []
        date_groups[date_key].append(avail)
    
    overlaps = []
    
    for date_str, date_availabilities in date_groups.items():
        # Skip if less than 2 people available on this date
        if len(date_availabilities) < 2:
            continue
        
        date_obj = datetime.fromisoformat(date_str).date()
        
        # Handle all-day availability
        all_day_count = sum(1 for avail in date_availabilities if avail.all_day)
        if all_day_count >= 2:
            overlaps.append({
                'date': date_obj,
                'start_time': None,
                'end_time': None,
                'all_day': True,
                'guest_count': all_day_count,
                'confidence': 'high'
            })
            continue
        
        # Find time slot overlaps
        time_slots = []
        for avail in date_availabilities:
            if not avail.all_day and avail.start_time and avail.end_time:
                time_slots.append({
                    'start': avail.start_time,
                    'end': avail.end_time,
                    'guest': avail.guest,
                    'preference': avail.preference_level
                })
        
        if len(time_slots) < 2:
            continue
        
        # Find overlapping time ranges
        slot_overlaps = find_time_slot_overlaps(time_slots)
        
        for overlap in slot_overlaps:
            overlaps.append({
                'date': date_obj,
                'start_time': overlap['start'],
                'end_time': overlap['end'],
                'all_day': False,
                'guest_count': overlap['guest_count'],
                'confidence': overlap['confidence'],
                'duration_hours': overlap['duration_hours']
            })
    
    # Sort by date and guest count (descending)
    overlaps.sort(key=lambda x: (x['date'], -x['guest_count']))
    
    return overlaps


def find_time_slot_overlaps(time_slots: List[Dict]) -> List[Dict[str, Any]]:
    """
    Find overlapping time periods from a list of time slots.
    
    Args:
        time_slots: List of time slot dictionaries
        
    Returns:
        list: List of overlapping periods
    """
    overlaps = []
    
    # Convert time slots to datetime for easier comparison
    datetime_slots = []
    base_date = datetime.now().date()
    
    for slot in time_slots:
        start_dt = datetime.combine(base_date, slot['start'])
        end_dt = datetime.combine(base_date, slot['end'])
        datetime_slots.append({
            'start': start_dt,
            'end': end_dt,
            'guest': slot['guest'],
            'preference': slot['preference']
        })
    
    # Check all pairs for overlaps
    for i in range(len(datetime_slots)):
        for j in range(i + 1, len(datetime_slots)):
            slot1 = datetime_slots[i]
            slot2 = datetime_slots[j]
            
            # Find overlap
            overlap_start = max(slot1['start'], slot2['start'])
            overlap_end = min(slot1['end'], slot2['end'])
            
            if overlap_start < overlap_end:
                duration = (overlap_end - overlap_start).total_seconds() / 3600
                
                # Only include overlaps of at least 1 hour
                if duration >= 1:
                    overlaps.append({
                        'start': overlap_start.time(),
                        'end': overlap_end.time(),
                        'guest_count': 2,
                        'duration_hours': duration,
                        'confidence': 'medium',
                        'guests': [slot1['guest'], slot2['guest']]
                    })
    
    # Remove duplicate overlaps and merge adjacent ones
    merged_overlaps = merge_adjacent_overlaps(overlaps)
    
    return merged_overlaps


def merge_adjacent_overlaps(overlaps: List[Dict]) -> List[Dict]:
    """
    Merge adjacent or overlapping time periods.
    
    Args:
        overlaps: List of overlap dictionaries
        
    Returns:
        list: Merged overlaps
    """
    if not overlaps:
        return []
    
    # Sort by start time
    sorted_overlaps = sorted(overlaps, key=lambda x: x['start'])
    
    merged = [sorted_overlaps[0]]
    
    for current in sorted_overlaps[1:]:
        last_merged = merged[-1]
        
        # Check if current overlap is adjacent or overlapping with the last merged
        if current['start'] <= last_merged['end']:
            # Merge them
            merged[-1] = {
                'start': last_merged['start'],
                'end': max(last_merged['end'], current['end']),
                'guest_count': max(last_merged['guest_count'], current['guest_count']),
                'duration_hours': (
                    datetime.combine(datetime.min.date(), max(last_merged['end'], current['end'])) -
                    datetime.combine(datetime.min.date(), last_merged['start'])
                ).total_seconds() / 3600,
                'confidence': 'high' if last_merged['confidence'] == 'high' or current['confidence'] == 'high' else 'medium',
                'guests': list(set(last_merged.get('guests', []) + current.get('guests', [])))
            }
        else:
            merged.append(current)
    
    return merged


def parse_natural_time_range(text: str) -> List[Dict[str, Any]]:
    """
    Parse natural language time expressions into structured time ranges.
    
    Args:
        text: Natural language time description
        
    Returns:
        list: List of parsed time ranges
    """
    text = text.lower().strip()
    time_ranges = []
    
    # Common time patterns
    time_patterns = {
        'morning': {'start': '09:00', 'end': '12:00'},
        'early morning': {'start': '07:00', 'end': '10:00'},
        'late morning': {'start': '10:00', 'end': '12:00'},
        'afternoon': {'start': '12:00', 'end': '17:00'},
        'early afternoon': {'start': '12:00', 'end': '15:00'},
        'late afternoon': {'start': '15:00', 'end': '17:00'},
        'evening': {'start': '17:00', 'end': '21:00'},
        'early evening': {'start': '17:00', 'end': '19:00'},
        'late evening': {'start': '19:00', 'end': '21:00'},
        'night': {'start': '21:00', 'end': '23:59'},
        'lunch time': {'start': '11:30', 'end': '13:30'},
        'dinner time': {'start': '18:00', 'end': '20:00'},
        'business hours': {'start': '09:00', 'end': '17:00'},
        'after work': {'start': '17:30', 'end': '21:00'},
    }
    
    # Check for known time patterns
    for pattern, times in time_patterns.items():
        if pattern in text:
            start_time = datetime.strptime(times['start'], '%H:%M').time()
            end_time = datetime.strptime(times['end'], '%H:%M').time()
            
            time_ranges.append({
                'start_time': start_time,
                'end_time': end_time,
                'all_day': False,
                'confidence': 'high',
                'source': pattern
            })
    
    # Parse specific time formats (e.g., "2pm-5pm", "14:00-17:00")
    time_regex_patterns = [
        r'(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})',  # 14:00-17:00
        r'(\d{1,2})\s*(am|pm)\s*-\s*(\d{1,2})\s*(am|pm)',  # 2pm-5pm
        r'(\d{1,2})\s*-\s*(\d{1,2})\s*(am|pm)',  # 2-5pm
    ]
    
    for pattern in time_regex_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                groups = match.groups()
                
                if len(groups) == 4 and groups[1] in ['am', 'pm']:  # 2pm-5pm format
                    start_hour = int(groups[0])
                    start_period = groups[1].lower()
                    end_hour = int(groups[2])
                    end_period = groups[3].lower()
                    
                    # Convert to 24-hour format
                    if start_period == 'pm' and start_hour != 12:
                        start_hour += 12
                    elif start_period == 'am' and start_hour == 12:
                        start_hour = 0
                    
                    if end_period == 'pm' and end_hour != 12:
                        end_hour += 12
                    elif end_period == 'am' and end_hour == 12:
                        end_hour = 0
                    
                    start_time = datetime.strptime(f'{start_hour:02d}:00', '%H:%M').time()
                    end_time = datetime.strptime(f'{end_hour:02d}:00', '%H:%M').time()
                    
                elif len(groups) == 4:  # 14:00-17:00 format
                    start_time = datetime.strptime(f'{groups[0]}:{groups[1]}', '%H:%M').time()
                    end_time = datetime.strptime(f'{groups[2]}:{groups[3]}', '%H:%M').time()
                
                else:
                    continue
                
                time_ranges.append({
                    'start_time': start_time,
                    'end_time': end_time,
                    'all_day': False,
                    'confidence': 'high',
                    'source': 'regex_parse'
                })
                
            except (ValueError, IndexError):
                continue
    
    # Check for all-day indicators
    all_day_indicators = ['all day', 'any time', 'whole day', 'entire day', 'flexible']
    if any(indicator in text for indicator in all_day_indicators):
        time_ranges.append({
            'start_time': None,
            'end_time': None,
            'all_day': True,
            'confidence': 'high',
            'source': 'all_day'
        })
    
    # If no specific times found, return a default range
    if not time_ranges:
        time_ranges.append({
            'start_time': None,
            'end_time': None,
            'all_day': True,
            'confidence': 'low',
            'source': 'default'
        })
    
    return time_ranges


def suggest_optimal_time_slots(overlaps: List[Dict], event_duration_hours: float = 2.0) -> List[Dict]:
    """
    Suggest optimal time slots based on overlapping availability.
    
    Args:
        overlaps: List of overlapping availability periods
        event_duration_hours: Desired event duration in hours
        
    Returns:
        list: Suggested time slots ranked by suitability
    """
    suggestions = []
    
    for overlap in overlaps:
        if overlap['all_day']:
            # For all-day availability, suggest common time slots
            common_slots = [
                {'start': '10:00', 'end': '12:00', 'name': 'Late Morning'},
                {'start': '14:00', 'end': '16:00', 'name': 'Early Afternoon'},
                {'start': '18:00', 'end': '20:00', 'name': 'Early Evening'},
            ]
            
            for slot in common_slots:
                start_time = datetime.strptime(slot['start'], '%H:%M').time()
                end_time = datetime.strptime(slot['end'], '%H:%M').time()
                
                suggestions.append({
                    'date': overlap['date'],
                    'start_time': start_time,
                    'end_time': end_time,
                    'duration_hours': 2.0,
                    'guest_count': overlap['guest_count'],
                    'confidence': overlap['confidence'],
                    'name': f"{slot['name']} on {overlap['date'].strftime('%A, %B %d')}",
                    'score': overlap['guest_count'] * 10
                })
        else:
            # For specific time overlaps, check if duration fits
            available_duration = overlap['duration_hours']
            
            if available_duration >= event_duration_hours:
                suggestions.append({
                    'date': overlap['date'],
                    'start_time': overlap['start_time'],
                    'end_time': overlap['end_time'],
                    'duration_hours': available_duration,
                    'guest_count': overlap['guest_count'],
                    'confidence': overlap['confidence'],
                    'name': f"{overlap['start_time'].strftime('%I:%M %p')} - {overlap['end_time'].strftime('%I:%M %p')} on {overlap['date'].strftime('%A, %B %d')}",
                    'score': overlap['guest_count'] * available_duration
                })
    
    # Sort suggestions by score (guest count and duration)
    suggestions.sort(key=lambda x: x['score'], reverse=True)
    
    return suggestions[:5]  # Return top 5 suggestions
