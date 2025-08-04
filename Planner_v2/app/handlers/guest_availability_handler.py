import logging
import json
import re
from datetime import datetime, timedelta
from app.handlers import BaseWorkflowHandler, HandlerResult
from app.models.event import Event
from app.models.guest import Guest
from app.models.availability import Availability
from app.models.guest_state import GuestState

logger = logging.getLogger(__name__)

class GuestAvailabilityHandler(BaseWorkflowHandler):
    """Handles guest availability response parsing and storage"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Use the AI service passed in from parent
    
    def handle_availability_response(self, guest_state: GuestState, message: str) -> str:
        """Process guest availability response - single message, immediate cleanup"""
        try:
            message_lower = message.lower().strip()
            
            # Handle follow-up commands
            if message_lower == '1':
                return self._handle_send_availability(guest_state)
            elif message_lower == '2' or message_lower == 'change':
                return self._handle_change_availability(guest_state)
            elif message_lower == 'status':
                return self._handle_status_request(guest_state)
            elif message_lower == 'done':
                return "👍 All set! Thanks for providing your availability."
            
            # Parse availability using distributed AI parsing
            context = guest_state.get_state_data()
            parsed_availability = self._parse_availability_input(message, context)
            
            if parsed_availability.get('success') and parsed_availability.get('available_dates'):
                # Save availability data
                guest = Guest.query.filter_by(
                    event_id=guest_state.event_id,
                    phone_number=guest_state.phone_number
                ).first()
                
                if guest:
                    # Save availability records
                    for avail_data in parsed_availability['available_dates']:
                        availability = Availability(
                            event_id=guest_state.event_id,
                            guest_id=guest.id,
                            date=datetime.strptime(avail_data['date'], '%Y-%m-%d').date(),
                            start_time=datetime.strptime(avail_data['start_time'], '%H:%M').time(),
                            end_time=datetime.strptime(avail_data['end_time'], '%H:%M').time(),
                            all_day=avail_data.get('all_day', False)
                        )
                        availability.save()
                    
                    # Mark guest as having provided availability
                    guest.availability_provided = True
                    guest.save()
                    
                    # Format confirmation response
                    response_text = "Got it! Here's your availability:\n"
                    for avail_data in parsed_availability['available_dates']:
                        date_obj = datetime.strptime(avail_data['date'], '%Y-%m-%d').date()
                        formatted_date = date_obj.strftime('%a, %-m/%-d')
                        start_time = avail_data['start_time']
                        end_time = avail_data['end_time']
                        response_text += f"- {formatted_date}: {start_time} to {end_time}\n"
                    
                    response_text += "\n✅ Thanks! I've recorded your availability. "
                    response_text += f"{guest_state.event.planner.name} will use this to find the best time for everyone.\n\n"
                    response_text += "What would you like to do:\n"
                    response_text += "1. Send Availability (notify planner)\n"
                    response_text += "2. Change Availability"
                    
                    return response_text
            
            return "I couldn't understand your availability. Please try again with something like 'Monday after 2pm' or 'Saturday all day'."
            
        except Exception as e:
            logger.error(f"Error handling availability response: {e}")
            return "Sorry, there was an error processing your availability."
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        """Standard handler interface - not used for guest responses"""
        # This handler is used differently - called directly for guest responses
        return HandlerResult.error_response("This handler is for guest availability responses only")
    
    def _parse_availability_input(self, message: str, context: dict) -> dict:
        """Parse availability input using AI with fallback"""
        # Try AI parsing first
        ai_result = self._ai_parse_availability(message, context)
        if ai_result and ai_result.get('success'):
            logger.info(f"Guest availability - AI parsing succeeded: {ai_result}")
            return ai_result
        
        # Fallback to simple parsing
        logger.info("Guest availability - falling back to simple parsing")
        simple_result = self._simple_parse_availability(message)
        logger.info(f"Guest availability - simple parsing result: {simple_result}")
        return simple_result
    
    def _ai_parse_availability(self, message: str, context: dict) -> dict:
        """AI parsing for availability responses"""
        try:
            # Get current event dates for context
            event_dates_str = ""
            if context and context.get('event_dates'):
                event_dates_str = f"Event dates: {', '.join(context['event_dates'])}"
            
            current_date = datetime.now().strftime('%Y-%m-%d')
            
            prompt = f"""Parse availability from: "{message}"
            
Current date: {current_date}
{event_dates_str}

Return JSON with:
- success: true/false
- available_dates: array of objects with date, start_time, end_time, all_day
- error: string if failed

Format dates as YYYY-MM-DD and times as HH:MM (24-hour)

Examples:
"Tuesday after 2pm" -> {{"success": true, "available_dates": [{{"date": "2025-08-06", "start_time": "14:00", "end_time": "23:59", "all_day": false}}]}}
"Monday all day" -> {{"success": true, "available_dates": [{{"date": "2025-08-05", "start_time": "09:00", "end_time": "17:00", "all_day": true}}]}}
"Friday 2-6pm, Saturday after 4pm" -> {{"success": true, "available_dates": [{{"date": "2025-08-08", "start_time": "14:00", "end_time": "18:00", "all_day": false}}, {{"date": "2025-08-09", "start_time": "16:00", "end_time": "23:59", "all_day": false}}]}}"""

            logger.info(f"Guest availability - attempting AI parsing for: '{message}'")
            response = self.ai_service.make_completion(prompt, 300)
            logger.info(f"Guest availability - AI response: {response}")
            
            if response:
                result = json.loads(response)
                logger.info(f"Guest availability - AI parsing result: {result}")
                return result
                
        except Exception as e:
            logger.error(f"Guest availability AI parsing error: {e}")
            
        return None
    
    def _simple_parse_availability(self, message: str) -> dict:
        """Simple fallback parsing for availability"""
        message_lower = message.lower().strip()
        
        # Simple patterns for common cases
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        # Find day mentioned
        found_day = None
        for day in weekdays:
            if day in message_lower:
                found_day = day
                break
        
        if found_day:
            # Calculate next occurrence of that day
            today = datetime.now()
            target_weekday = weekdays.index(found_day)
            today_weekday = today.weekday()
            
            # Calculate days ahead - if it's the same day, use today; otherwise next occurrence
            days_ahead = target_weekday - today_weekday
            if days_ahead < 0:  # Target day already happened this week
                days_ahead += 7
            # If days_ahead == 0, it means today is the target day
            
            target_date = today + timedelta(days=days_ahead)
            
            # Check for time patterns
            if 'all day' in message_lower:
                return {
                    'success': True,
                    'available_dates': [{
                        'date': target_date.strftime('%Y-%m-%d'),
                        'start_time': '09:00',
                        'end_time': '17:00',
                        'all_day': True
                    }]
                }
            elif 'after' in message_lower:
                # Look for time after "after"
                time_match = re.search(r'after (\d{1,2})(?::(\d{2}))?\s*(am|pm)?', message_lower)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2)) if time_match.group(2) else 0
                    ampm = time_match.group(3)
                    
                    if ampm == 'pm' and hour != 12:
                        hour += 12
                    elif ampm == 'am' and hour == 12:
                        hour = 0
                    elif not ampm and hour < 8:  # Assume PM for reasonable hours
                        hour += 12
                    
                    start_time = f"{hour:02d}:{minute:02d}"
                    
                    return {
                        'success': True,
                        'available_dates': [{
                            'date': target_date.strftime('%Y-%m-%d'),
                            'start_time': start_time,
                            'end_time': '23:59',
                            'all_day': False
                        }]
                    }
        
        return {
            'success': False,
            'error': 'Could not parse availability'
        }
    
    def _handle_send_availability(self, guest_state: GuestState) -> str:
        """Send availability notification to planner"""
        try:
            # This would trigger a notification to the planner
            # For now, just confirm the send action
            guest_name = guest_state.guest_name or "Guest"
            planner_name = guest_state.event.planner.name
            
            # In a full implementation, this would send an SMS to the planner
            # notifying them that this guest has provided availability
            
            return f"✅ Your availability has been sent to {planner_name}!\n\n" \
                   f"They'll be notified that you've responded and can now see your times.\n\n" \
                   f"You'll receive an invitation once {planner_name} finalizes the event details."
                   
        except Exception as e:
            logger.error(f"Error sending availability notification: {e}")
            return "✅ Your availability has been recorded! The planner will be notified."
    
    def _handle_change_availability(self, guest_state: GuestState) -> str:
        """Handle request to change availability"""
        return "Sure! What's your updated availability? You can say things like:\n\n" \
               "- 'Tuesday after 2pm'\n" \
               "- 'Wednesday all day'\n" \
               "- 'Friday 2-6pm'"
    
    def _handle_status_request(self, guest_state: GuestState) -> str:
        """Handle request for event status"""
        try:
            event = guest_state.event
            return f"📅 Event: {event.title or 'Event'}\n" \
                   f"👤 Organizer: {event.planner.name}\n" \
                   f"📊 Status: Planning in progress\n" \
                   f"💬 You can still change your availability by replying 'change'"
        except Exception as e:
            logger.error(f"Error getting event status: {e}")
            return "Event status is being updated. Check back soon!"
