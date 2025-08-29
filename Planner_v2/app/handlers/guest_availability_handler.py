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
        from app.services.sms_service import SMSService
        self.sms_service = SMSService()
    
    def handle_availability_response(self, guest_state: GuestState, message: str) -> str:
        """Process guest availability response - multi-step interaction"""
        try:
            message_lower = message.lower().strip()
            
            # Check if user is in confirmation menu state
            state_data = guest_state.get_state_data()
            is_in_menu_confirmation = state_data.get('awaiting_menu_choice', False)
            
            # Handle follow-up commands (these should clean up the guest state)
            if message_lower == '1':
                # Check if this is availability confirmation or final confirmation
                if is_in_menu_confirmation:
                    return self._handle_confirm_availability(guest_state)
                else:
                    # This might be final confirmation - check state
                    state_data = guest_state.get_state_data()
                    if state_data.get('awaiting_final_choice', False):
                        return self._handle_send_final_availability(guest_state)
            elif message_lower == '2':
                # Check if this is change availability or change preferences  
                if is_in_menu_confirmation:
                    return self._handle_change_availability(guest_state)
                else:
                    # This might be final confirmation - change availability
                    state_data = guest_state.get_state_data()
                    if state_data.get('awaiting_final_choice', False):
                        return self._handle_change_availability_final(guest_state)
            elif message_lower == '3':
                # This should be change preferences in final confirmation
                state_data = guest_state.get_state_data()
                if state_data.get('awaiting_final_choice', False):
                    return self._handle_change_preferences(guest_state)
                # Keep guest state active for new availability input
            elif message_lower == 'status':
                return self._handle_status_request(guest_state)
            elif message_lower == 'done':
                # Mark guest state for cleanup - let SMS router handle actual deletion
                guest_state.current_state = 'completed'
                guest_state.save()
                return "👍 All set! Thanks for providing your availability."
            elif message_lower in ['busy', 'not available', 'unavailable', 'can\'t make it', 'cant make it']:
                # Handle guests who are not available for any of the proposed days
                return self._handle_busy_response(guest_state)
            
            # Check if we're awaiting preferences
            state_data = guest_state.get_state_data()
            if guest_state.current_state == 'awaiting_preferences':
                return self._handle_preferences_response(guest_state, message)
            
            # If user is in menu confirmation state and didn't choose 1 or 2, give menu error
            if is_in_menu_confirmation:
                return "Please respond with '1' or '2':\n\n1. Confirm availability\n2. Change availability"
            
            # Parse availability using distributed AI parsing
            context = guest_state.get_state_data()
            logger.info(f"Guest availability parsing - context: {context}")
            parsed_availability = self._parse_availability_input(message, context)
            logger.info(f"Guest availability parsing - result: {parsed_availability}")
            
            if parsed_availability.get('success') and parsed_availability.get('available_dates'):
                # Validate availability entries before saving
                valid_entries = []
                invalid_entries = []
                
                for avail_data in parsed_availability['available_dates']:
                    validation_result = self._validate_availability_entry(avail_data)
                    if validation_result['valid']:
                        valid_entries.append(avail_data)
                    else:
                        invalid_entries.append({
                            'data': avail_data,
                            'error': validation_result['error']
                        })
                
                # If we have invalid entries, ask for clarification
                if invalid_entries and not valid_entries:
                    error_msg = "I couldn't understand your availability. Please check these issues:\n\n"
                    for invalid in invalid_entries:
                        error_msg += f"• {invalid['error']}\n"
                    error_msg += "\nPlease try again with clearer times, like:\n"
                    error_msg += "- 'Monday 2pm to 6pm'\n"
                    error_msg += "- 'Monday afternoon'\n"
                    error_msg += "- 'Monday after 2pm'"
                    return error_msg
                
                # If we have some valid entries, use those and warn about invalid ones
                if invalid_entries:
                    logger.warning(f"Some availability entries were invalid: {invalid_entries}")
                
                # Continue with valid entries only
                if valid_entries:
                    # Save availability data - handle phone number format mismatch
                    # Guest state has normalized phone, but Guest record might have formatted phone
                    guest = Guest.query.filter_by(
                    event_id=guest_state.event_id,
                    phone_number=guest_state.phone_number
                ).first()
                
                # If not found, try with +1 prefix format
                if not guest:
                    formatted_phone = f"+1{guest_state.phone_number}"
                    guest = Guest.query.filter_by(
                        event_id=guest_state.event_id,
                        phone_number=formatted_phone
                    ).first()
                
                if guest:
                    # Use the safer availability service to prevent duplicates
                    from app.services.availability_service import AvailabilityService
                    availability_service = AvailabilityService()
                    
                    success = availability_service.update_guest_availability(
                        guest_id=guest.id,
                        event_id=guest_state.event_id,
                        availability_data=valid_entries
                    )
                    
                    if success:
                        # Don't mark as complete yet - we need preferences first
                        # guest.availability_provided = True  # Comment out this line
                        # guest.save()
                        pass
                    
                    # Format confirmation response
                    response_text = "Got it! Here's what I recorded:\n\n"
                    response_text += "📅 Your availability:\n"
                    for avail_data in valid_entries:
                        date_obj = datetime.strptime(avail_data['date'], '%Y-%m-%d').date()
                        # Format as day name with readable time
                        day_name = date_obj.strftime('%A')
                        start_time = self._format_time_12hr(avail_data['start_time'])
                        end_time = self._format_time_12hr(avail_data['end_time'])
                        response_text += f"- {day_name} {start_time}-{end_time}\n"
                    
                    response_text += "\n1. Confirm availability\n"
                    response_text += "2. Change availability"
                    
                    # Mark that user is now awaiting menu choice
                    state_data = guest_state.get_state_data()
                    state_data['awaiting_menu_choice'] = True
                    state_data['availability_data'] = valid_entries  # Store for later use
                    guest_state.set_state_data(state_data)
                    guest_state.save()
                    
                    return response_text
            
            return "I couldn't understand your availability. Please try again with something like:\n\n• 'Saturday after 6pm'\n• 'Saturday all day'\n• 'Saturday 2-6pm'"
            
        except Exception as e:
            logger.error(f"Error getting event status: {e}")
            return "Sorry, I couldn't get the event status right now."
    
    def _extract_first_name(self, full_name: str) -> str:
        """Extract first name from full name, handling titles"""
        if not full_name:
            return "Friend"
        
        # Split by spaces and clean up
        name_parts = full_name.strip().split()
        if not name_parts:
            return full_name.strip() or "Friend"
        
        # Common titles to skip
        titles = {'dr.', 'dr', 'mr.', 'mr', 'mrs.', 'mrs', 'ms.', 'ms', 'prof.', 'prof'}
        
        # Find the first non-title word
        for part in name_parts:
            if part.lower().rstrip('.') not in titles:
                return part
        
        # If all parts are titles, just use the first one
        return name_parts[0]

    def _format_guest_availability_details(self, guest: Guest) -> str:
        """Format guest's availability details for planner notification"""
        try:
            from app.models.availability import Availability
            from datetime import datetime
            
            # Get all availability records for this guest
            availability_records = Availability.query.filter_by(
                event_id=guest.event_id,
                guest_id=guest.id
            ).all()
            
            if not availability_records:
                return "- No specific times provided"
            
            # Group by date and format
            availability_lines = []
            
            for avail in availability_records:
                if avail.date:
                    # Format date as "Friday"
                    date_str = avail.date.strftime('%A')
                    
                    if avail.all_day:
                        availability_lines.append(f"- {date_str} all day")
                    else:
                        # Format times in 12-hour format
                        start_time = self._format_time_12hr(avail.start_time.strftime('%H:%M'))
                        end_time = self._format_time_12hr(avail.end_time.strftime('%H:%M'))
                        availability_lines.append(f"- {date_str} {start_time}-{end_time}")
            
            if not availability_lines:
                return "- No specific times provided"
            
            # Return just the availability lines - preferences handled separately in notifications
            result = '\n'.join(availability_lines)
            
            return result
            
        except Exception as e:
            logger.error(f"Error formatting guest availability details: {e}")
            return "- Availability provided"

    def _send_planner_notification(self, guest_state: GuestState, guest: Guest) -> None:
        """Send immediate notification to planner when guest provides availability"""
        try:
            planner_name = guest_state.event.planner.name
            guest_name = self._extract_first_name(guest.name)
            
            # Get guest's availability details
            availability_details = self._format_guest_availability_details(guest)
            
            # Count remaining guests who haven't responded
            total_guests = Guest.query.filter_by(event_id=guest_state.event_id).count()
            responded_guests = Guest.query.filter_by(
                event_id=guest_state.event_id, 
                availability_provided=True
            ).count()
            remaining_guests = total_guests - responded_guests
            
            # Create planner notification message
            if remaining_guests > 0:
                planner_message = f"✅ {guest_name} has provided their availability:\n\n{availability_details}\n\n"
                planner_message += f"📊 {responded_guests}/{total_guests} guests have responded\n"
                planner_message += f"⏳ Waiting for {remaining_guests} more guest" + ("s" if remaining_guests != 1 else "") + "\n\n"
                planner_message += f"Press 1 to view current overlaps"
            else:
                planner_message = f"✅ {guest_name} has provided their availability:\n{availability_details}\n\n"
                planner_message += f"🎉 Everyone has responded!\n\n"
                planner_message += "Would you like to:\n"
                planner_message += "1. Pick a time\n"
                planner_message += "2. Add more guests"
            
            # Send SMS to planner
            planner_phone = guest_state.event.planner.phone_number
            self.sms_service.send_sms(planner_phone, planner_message)
            logger.info(f"Sent planner notification to {planner_phone} about {guest_name}'s availability")
            
        except Exception as e:
            logger.error(f"Error sending planner notification: {e}")
    
    def _format_time_12hr(self, time_str: str) -> str:
        """Convert 24-hour format to 12-hour format"""
        try:
            # Parse the time string (HH:MM format)
            time_obj = datetime.strptime(time_str, '%H:%M')
            # Format to 12-hour with am/pm
            formatted = time_obj.strftime('%I:%M%p').lower()
            # Remove leading zero from hour and :00 for cleaner look
            if formatted.startswith('0'):
                formatted = formatted[1:]  # Remove leading zero
            # Remove :00 for on-the-hour times (12:00pm becomes 12pm)
            if ':00' in formatted:
                formatted = formatted.replace(':00', '')
            return formatted
        except ValueError:
            # If parsing fails, return original
            return time_str

    def handle_message(self, event: Event, message: str) -> HandlerResult:
        """Standard handler interface - not used for guest responses"""
        # This handler is used differently - called directly for guest responses
        return HandlerResult.error_response("This handler is for guest availability responses only")
    
    def _parse_availability_input(self, message: str, context: dict) -> dict:
        """Parse availability input using AI with fallback"""
        # Pre-validate input for obvious gibberish
        if not self._is_valid_availability_input(message, context):
            return {
                'success': False,
                'error': 'Could not understand your availability. Please use clear day names and times.'
            }
        
        # Try AI parsing first
        ai_result = self._ai_parse_availability(message, context)
        if ai_result and ai_result.get('success'):
            logger.info(f"Guest availability - AI parsing successful: {ai_result}")
            return ai_result
        
        # Fall back to simple parsing
        logger.info("Guest availability - AI failed, using simple parsing")
        simple_result = self._simple_parse_availability(message, context)
        logger.info(f"Guest availability - simple parsing result: {simple_result}")
        return simple_result
    
    def _ai_parse_availability(self, message: str, context: dict) -> dict:
        """AI parsing for availability responses"""
        try:
            # Get current event dates for context with day names
            event_dates_context = ""
            if context and context.get('event_dates'):
                date_mappings = []
                for date_str in context['event_dates']:
                    try:
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                        day_name = date_obj.strftime('%A')
                        formatted_date = date_obj.strftime('%B %-d')
                        date_mappings.append(f"{day_name} = {date_str} ({formatted_date})")
                    except ValueError:
                        date_mappings.append(f"{date_str}")
                event_dates_context = f"Available dates: {', '.join(date_mappings)}"
            
            current_date = datetime.now().strftime('%Y-%m-%d')
            current_day = datetime.now().strftime('%A, %B %-d, %Y')
            
            # Check if this is a single-day event
            is_single_day = context and context.get('event_dates') and len(context['event_dates']) == 1
            single_day_instructions = ""
            
            if is_single_day:
                single_day_date = context['event_dates'][0]
                try:
                    date_obj = datetime.strptime(single_day_date, '%Y-%m-%d')
                    day_name = date_obj.strftime('%A')
                    formatted_date = date_obj.strftime('%B %-d')
                    single_day_instructions = f"""
SPECIAL SINGLE-DAY EVENT INSTRUCTIONS:
This event only has ONE date: {day_name} = {single_day_date} ({formatted_date})

For this single-day event, accept time-only inputs WITHOUT day names:
- "2-4" = {single_day_date} 2:00pm-4:00pm (14:00-16:00)
- "2-4pm" = {single_day_date} 2:00pm-4:00pm (14:00-16:00)
- "from 2-4" = {single_day_date} 2:00pm-4:00pm (14:00-16:00)
- "afternoon" = {single_day_date} 12:00pm-6:00pm (12:00-18:00)
- "morning" = {single_day_date} 8:00am-12:00pm (08:00-12:00)
- "after 2pm" = {single_day_date} 2:00pm-11:59pm (14:00-23:59)
- "all day" = {single_day_date} 8:00am-11:59pm (08:00-23:59)

When user provides only times/periods without mentioning the day, use the single event date: {single_day_date}
"""
                except ValueError:
                    pass
            
            prompt = f"""Parse availability from: "{message}"
            
Current date: {current_date} ({current_day})
{event_dates_context}
{single_day_instructions}

CRITICAL: Use the exact dates provided above. Match day names to the correct dates.
Only create availability for dates that are listed in the available event dates above.
If user mentions a day that doesn't match any event date, ignore it.

IMPORTANT: When user mentions ANY day name (Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday), 
they mean the specific date from the event dates list above, NOT the next occurrence of that day.
Examples:
- "Monday" = the Monday date from the event dates list
- "Tuesday" = the Tuesday date from the event dates list  
- "Wednesday" = the Wednesday date from the event dates list
- "Thursday" = the Thursday date from the event dates list
- "Friday" = the Friday date from the event dates list
- "Saturday" = the Saturday date from the event dates list
- "Sunday" = the Sunday date from the event dates list

Common availability patterns:
- "Friday afternoon" = Friday 12:00pm-6:00pm (12:00-18:00)
- "Friday after 2pm" = Friday 2:00pm-11:59pm (14:00-23:59)
- "Friday morning" = Friday 8:00am-12:00pm (08:00-12:00)
- "Friday evening" = Friday 6:00pm-10:00pm (18:00-22:00)
- "Friday all day" = Friday 8:00am-11:59pm (08:00-23:59)
- "Friday 2-6pm" = Friday 2:00pm-6:00pm (14:00-18:00)

CRITICAL TIME PARSING RULES:
- "p" means PM, "a" means AM (e.g., "7p" = 7:00pm, "11a" = 11:00am)
- If no a/p specified and time is 1-12, assume reasonable times:
  * "11-5" = 11:00am to 5:00pm (11:00-17:00)
  * "7-11" = 7:00pm to 11:00pm (19:00-23:00) 
  * "2-6" = 2:00pm to 6:00pm (14:00-18:00)
- "7-11p" = 7:00pm to 11:00pm (19:00-23:00)
- "11-5" or "11a-5p" = 11:00am to 5:00pm (11:00-17:00)
- "Friday 7-11p, Saturday 11-5" = Friday 7pm-11pm AND Saturday 11am-5pm

SHORTHAND TIME EXAMPLES:
- "7p" = 7:00pm (19:00)
- "11a" = 11:00am (11:00)  
- "7-11p" = 7:00pm-11:00pm (19:00-23:00)
- "11-5" = 11:00am-5:00pm (11:00-17:00)
- "2-6" = 2:00pm-6:00pm (14:00-18:00)
- "9-11" = 9:00pm-11:00pm (21:00-23:00)

CRITICAL TIME RULES:
- start_time MUST be different from end_time (never the same)
- start_time MUST be before end_time
- Time slots must be at least 30 minutes long
- If user says "Monday afternoon 2pm", interpret as "Monday from 2pm to 6pm", NOT "2pm to 2pm"

Return JSON with:
- success: true/false
- available_dates: array of objects with date, start_time, end_time, all_day
- error: string if failed

Format dates as YYYY-MM-DD and times as HH:MM (24-hour)

Examples (using actual event dates from context above):
"Friday afternoon" -> {{"success": true, "available_dates": [{{"date": "[FRIDAY_DATE]", "start_time": "12:00", "end_time": "18:00", "all_day": false}}]}}
"Friday after 2pm" -> {{"success": true, "available_dates": [{{"date": "[FRIDAY_DATE]", "start_time": "14:00", "end_time": "23:59", "all_day": false}}]}}
"Friday all day" -> {{"success": true, "available_dates": [{{"date": "[FRIDAY_DATE]", "start_time": "08:00", "end_time": "23:59", "all_day": true}}]}}
"Friday 7-11p" -> {{"success": true, "available_dates": [{{"date": "[FRIDAY_DATE]", "start_time": "19:00", "end_time": "23:00", "all_day": false}}]}}
"Saturday 11-5" -> {{"success": true, "available_dates": [{{"date": "[SATURDAY_DATE]", "start_time": "11:00", "end_time": "17:00", "all_day": false}}]}}
"Friday 7-11p, Saturday 11-5" -> {{"success": true, "available_dates": [{{"date": "[FRIDAY_DATE]", "start_time": "19:00", "end_time": "23:00", "all_day": false}}, {{"date": "[SATURDAY_DATE]", "start_time": "11:00", "end_time": "17:00", "all_day": false}}]}}"""

            logger.info(f"Guest availability - attempting AI parsing for: '{message}'")
            logger.info(f"Guest availability - sending prompt: {prompt}")
            response = self.ai_service.make_completion(prompt, 300)
            logger.info(f"Guest availability - AI response: '{response}'")
            logger.info(f"Guest availability - AI response type: {type(response)}")
            
            if response and response.strip():
                try:
                    # Extract JSON from response - AI sometimes adds extra text
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        result = json.loads(json_str)
                        logger.info(f"Guest availability - AI parsing result: {result}")
                        return result
                    else:
                        logger.error(f"Guest availability - No JSON found in AI response: '{response}'")
                except json.JSONDecodeError as je:
                    logger.error(f"Guest availability - JSON parsing error: {je}, Response: '{response}'")
            else:
                logger.error(f"Guest availability - AI returned empty/None response for input: '{message}'")
                
        except Exception as e:
            logger.error(f"Guest availability AI parsing error: {e}")
            
        return None
    
    def _simple_parse_availability(self, message: str, context: dict = None) -> dict:
        """Simple fallback parsing for availability - handles complex inputs like 'Friday after 2pm and Saturday all day'"""
        message_lower = message.lower().strip()
        available_dates = []
        
        # Check if this is a single-day event
        is_single_day = False
        single_day_date = None
        if context and context.get('event_dates'):
            is_single_day = len(context['event_dates']) == 1
            if is_single_day:
                single_day_date = context['event_dates'][0]
        
        # Split on "and" to handle multiple availability specs
        specs = [spec.strip() for spec in message_lower.split(' and ')]
        
        for spec in specs:
            parsed_spec = self._parse_single_availability_spec(spec, single_day_date if is_single_day else None)
            if parsed_spec:
                available_dates.extend(parsed_spec)
        
        if available_dates:
            return {
                'success': True,
                'available_dates': available_dates
            }
        
        return {
            'success': False,
            'error': 'Could not parse availability'
        }
    
    def _parse_single_availability_spec(self, spec: str, single_day_date: str = None) -> list:
        """Parse a single availability specification like 'friday after 2pm', 'saturday 7-11p', 'friday 11-5'"""
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        
        # Find day mentioned
        found_day = None
        for day in weekdays:
            if day in spec:
                found_day = day
                break
        
        # If no day found and we have a single day date, use that
        if not found_day and single_day_date:
            try:
                target_date = datetime.strptime(single_day_date, '%Y-%m-%d')
                # Parse time-only input for the single day
                return self._parse_time_only_spec(spec, target_date)
            except ValueError:
                return []
        
        if found_day:
            # Calculate next occurrence of that day
            today = datetime.now()
            target_weekday = weekdays.index(found_day)
            today_weekday = today.weekday()
            
            # Calculate days ahead - if it's the same day, use today; otherwise next occurrence
            days_ahead = target_weekday - today_weekday
            if days_ahead < 0:  # Target day already happened this week
                days_ahead += 7
            elif days_ahead == 0:  # Same day - use next week if it's late in the day
                if today.hour >= 18:  # After 6pm, assume they mean next week
                    days_ahead = 7
            
            target_date = today + timedelta(days=days_ahead)
            
            # Enhanced time pattern recognition
            # Check for shorthand time formats first (highest priority)
            time_range = self._parse_shorthand_time(spec)
            if time_range:
                return [{
                    'date': target_date.strftime('%Y-%m-%d'),
                    'start_time': time_range['start'],
                    'end_time': time_range['end'],
                    'all_day': False
                }]
            
            # Fallback to standard patterns
            if 'all day' in spec:
                return [{
                    'date': target_date.strftime('%Y-%m-%d'),
                    'start_time': '08:00',
                    'end_time': '23:59',
                    'all_day': True
                }]
            elif 'afternoon' in spec:
                return [{
                    'date': target_date.strftime('%Y-%m-%d'),
                    'start_time': '12:00',
                    'end_time': '18:00',
                    'all_day': False
                }]
            elif 'morning' in spec:
                return [{
                    'date': target_date.strftime('%Y-%m-%d'),
                    'start_time': '08:00',
                    'end_time': '12:00',
                    'all_day': False
                }]
            elif 'evening' in spec:
                return [{
                    'date': target_date.strftime('%Y-%m-%d'),
                    'start_time': '18:00',
                    'end_time': '22:00',
                    'all_day': False
                }]
            elif 'after' in spec:
                # Look for time after "after"
                time_match = re.search(r'after (\d{1,2})(?::(\d{2}))?\s*(am|pm)?', spec)
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
                    
                    return [{
                        'date': target_date.strftime('%Y-%m-%d'),
                        'start_time': start_time,
                        'end_time': '23:59',
                        'all_day': False
                    }]
        
        return []
    
    def _parse_shorthand_time(self, spec: str) -> dict:
        """Parse shorthand time formats like '7-11p', '11-5', '7p', etc."""
        import re
        
        spec = spec.strip().lower()
        
        # Pattern 1: Mixed am/pm ranges like "9a-12p" (9am to 12pm)
        mixed_pattern = r'(\d{1,2})\s*([ap])\s*-\s*(\d{1,2})\s*([ap])'
        mixed_match = re.search(mixed_pattern, spec)
        
        if mixed_match:
            start_num = int(mixed_match.group(1))
            start_period = mixed_match.group(2)
            end_num = int(mixed_match.group(3))
            end_period = mixed_match.group(4)
            
            # Convert to 24-hour
            if start_period == 'p':
                start_hour = 12 if start_num == 12 else start_num + 12
            else:  # 'a'
                start_hour = 0 if start_num == 12 else start_num
                
            if end_period == 'p':
                end_hour = 12 if end_num == 12 else end_num + 12
            else:  # 'a'
                end_hour = 0 if end_num == 12 else end_num
            
            if 0 <= start_hour <= 23 and 0 <= end_hour <= 23 and start_hour < end_hour:
                return {
                    'start': f"{start_hour:02d}:00",
                    'end': f"{end_hour:02d}:00"
                }
        
        # Pattern 2: Ranges with single am/pm: 7-11p, 2-6pm, 11-5
        range_pattern = r'(\d{1,2})\s*-\s*(\d{1,2})\s*([ap]m?)?'
        range_match = re.search(range_pattern, spec)
        
        if range_match:
            start_num = int(range_match.group(1))
            end_num = int(range_match.group(2))
            suffix = range_match.group(3)
            
            # Determine AM/PM for times
            if suffix and 'p' in suffix:
                # Both times are PM
                start_hour = 12 if start_num == 12 else start_num + 12
                end_hour = 12 if end_num == 12 else end_num + 12
            elif suffix and 'a' in suffix:
                # Both times are AM
                start_hour = 0 if start_num == 12 else start_num
                end_hour = 0 if end_num == 12 else end_num
            else:
                # No suffix - use smart defaults
                if start_num >= 7 and end_num <= 11 and start_num < end_num:
                    # Evening: 7-11 → 7pm-11pm
                    start_hour = start_num + 12
                    end_hour = end_num + 12
                elif start_num >= 11 and end_num <= 6:
                    # Day span: 11-5 → 11am-5pm
                    start_hour = start_num
                    end_hour = end_num + 12
                elif start_num >= 9 and end_num == 12:
                    # Morning: 9-12 → 9am-12pm
                    start_hour = start_num
                    end_hour = 12
                elif start_num >= 1 and start_num <= 6 and end_num > start_num:
                    # Afternoon: 1-6 → 1pm-6pm
                    start_hour = start_num + 12
                    end_hour = end_num + 12
                else:
                    # Default - assume PM if late hours
                    if start_num >= 6:
                        start_hour = start_num + 12
                        end_hour = end_num + 12
                    else:
                        start_hour = start_num
                        end_hour = end_num
            
            # Validate range
            if 0 <= start_hour <= 23 and 0 <= end_hour <= 23 and start_hour < end_hour:
                return {
                    'start': f"{start_hour:02d}:00",
                    'end': f"{end_hour:02d}:00"
                }
        
        # Pattern 3: Single times with am/pm: 7p, 11a, 2pm
        single_pattern = r'(\d{1,2})\s*([ap]m?)'
        single_match = re.search(single_pattern, spec)
        
        if single_match:
            time_num = int(single_match.group(1))
            suffix = single_match.group(2)
            
            if 'p' in suffix:
                hour = 12 if time_num == 12 else time_num + 12
            else:  # 'a' in suffix
                hour = 0 if time_num == 12 else time_num
            
            # For single times, assume 4-hour availability
            end_hour = min(23, hour + 4)
            
            if 0 <= hour <= 23:
                return {
                    'start': f"{hour:02d}:00",
                    'end': f"{end_hour:02d}:00"
                }
        
        return None
    
    def _parse_time_only_spec(self, spec: str, target_date: datetime) -> list:
        """Parse time-only specifications for single-day events like '2-4', '2-4pm', 'afternoon', etc."""
        import re
        
        spec = spec.strip().lower()
        
        # Remove "from" prefix if present
        spec = re.sub(r'^from\s+', '', spec)
        
        # Check for time periods first
        if 'afternoon' in spec:
            return [{
                'date': target_date.strftime('%Y-%m-%d'),
                'start_time': '12:00',
                'end_time': '18:00',
                'all_day': False
            }]
        elif 'morning' in spec:
            return [{
                'date': target_date.strftime('%Y-%m-%d'),
                'start_time': '08:00',
                'end_time': '12:00',
                'all_day': False
            }]
        elif 'evening' in spec:
            return [{
                'date': target_date.strftime('%Y-%m-%d'),
                'start_time': '18:00',
                'end_time': '22:00',
                'all_day': False
            }]
        elif 'all day' in spec or 'allday' in spec:
            return [{
                'date': target_date.strftime('%Y-%m-%d'),
                'start_time': '08:00',
                'end_time': '23:59',
                'all_day': True
            }]
        
        # Try shorthand time parsing for ranges
        time_range = self._parse_shorthand_time(spec)
        if time_range:
            return [{
                'date': target_date.strftime('%Y-%m-%d'),
                'start_time': time_range['start'],
                'end_time': time_range['end'],
                'all_day': False
            }]
        
        # Handle "after" patterns: "after 2pm", "after 2"
        after_match = re.search(r'after\s+(\d{1,2})(:\d{2})?\s*(am|pm)?', spec)
        if after_match:
            hour = int(after_match.group(1))
            minute = int(after_match.group(2)[1:]) if after_match.group(2) else 0
            ampm = after_match.group(3)
            
            if ampm == 'pm' and hour != 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            elif not ampm and hour < 8:  # Assume PM for reasonable hours
                hour += 12
            
            start_time = f"{hour:02d}:{minute:02d}"
            
            return [{
                'date': target_date.strftime('%Y-%m-%d'),
                'start_time': start_time,
                'end_time': '23:59',
                'all_day': False
            }]
        
        # Handle "before" patterns: "before 6pm", "before 6"
        before_match = re.search(r'before\s+(\d{1,2})(:\d{2})?\s*(am|pm)?', spec)
        if before_match:
            hour = int(before_match.group(1))
            minute = int(before_match.group(2)[1:]) if before_match.group(2) else 0
            ampm = before_match.group(3)
            
            if ampm == 'pm' and hour != 12:
                hour += 12
            elif ampm == 'am' and hour == 12:
                hour = 0
            elif not ampm and hour < 8:  # Assume PM for reasonable hours
                hour += 12
            
            end_time = f"{hour:02d}:{minute:02d}"
            
            return [{
                'date': target_date.strftime('%Y-%m-%d'),
                'start_time': '08:00',
                'end_time': end_time,
                'all_day': False
            }]
        
        return []
    
    def _handle_send_availability(self, guest_state: GuestState) -> str:
        """Send availability notification to planner"""
        try:
            # Get the guest record to get the name - handle phone number format mismatch
            guest = Guest.query.filter_by(
                event_id=guest_state.event_id,
                phone_number=guest_state.phone_number
            ).first()
            
            # If not found, try with +1 prefix format
            if not guest:
                formatted_phone = f"+1{guest_state.phone_number}"
                guest = Guest.query.filter_by(
                    event_id=guest_state.event_id,
                    phone_number=formatted_phone
                ).first()
            
            guest_name = self._extract_first_name(guest.name) if guest else "Guest"
            planner_name = guest_state.event.planner.name
            
            if guest and guest.availability_provided:
                # Check for late arrival - guest responding after planner moved past availability stage
                event = guest_state.event
                is_late_arrival = event.workflow_stage not in ['collecting_availability', 'tracking_availability']
                
                # Count remaining guests who haven't responded
                total_guests = Guest.query.filter_by(event_id=guest_state.event_id).count()
                responded_guests = Guest.query.filter_by(
                    event_id=guest_state.event_id, 
                    availability_provided=True
                ).count()
                remaining_guests = total_guests - responded_guests
                
                # Get guest's availability details
                availability_details = self._format_guest_availability_details(guest)
                
                if is_late_arrival:
                    # Late arrival - force planner back to overlap calculation
                    planner_message = f"🎉 {guest_name} has provided their availability:\n\n{availability_details}\n\n"
                    planner_message += "Everyone has responded!\n\n"
                    planner_message += "Would you like to:\n"
                    planner_message += "1. Pick a time\n"
                    planner_message += "2. Add more guests"
                    
                    # Force planner back to availability collection stage
                    event.workflow_stage = 'collecting_availability'
                    event.save()
                    
                elif remaining_guests > 0:
                    # Normal flow - still waiting for others
                    planner_message = f"✅ {guest_name} has provided their availability:\n\n{availability_details}\n\n"
                    planner_message += f"📊 {responded_guests}/{total_guests} guests have responded\n"
                    planner_message += f"⏳ Waiting for {remaining_guests} more guest" + ("s" if remaining_guests != 1 else "") + "\n\n"
                    planner_message += f"Press 1 to view current overlaps"
                else:
                    # Normal flow - everyone responded
                    planner_message = f"✅ {guest_name} has provided their availability:\n\n{availability_details}\n\n"
                    planner_message += f"🎉 Everyone has responded!\n\n"
                    planner_message += "Would you like to:\n"
                    planner_message += "1. Pick a time\n"
                    planner_message += "2. Add more guests"
                    
                    # Update event workflow stage to handle planner's next choice
                    event.workflow_stage = 'collecting_availability'
                    event.save()
                
                # Send SMS to planner
                planner_phone = guest_state.event.planner.phone_number
                self.sms_service.send_sms(planner_phone, planner_message)
            
            return f"✅ Thanks! I've recorded your availability for {planner_name}. They'll use this to find the best time for everyone."
                   
        except Exception as e:
            logger.error(f"Error sending availability notification: {e}")
            return "✅ Your availability has been recorded! The planner will be notified."
    
    def _handle_change_availability(self, guest_state: GuestState) -> str:
        """Handle request to change availability - keeps guest state active"""
        # Clear existing availability for this guest
        try:
            guest = Guest.query.filter_by(
                event_id=guest_state.event_id,
                phone_number=guest_state.phone_number
            ).first()
            
            if guest:
                # Remove existing availability records
                Availability.query.filter_by(
                    event_id=guest_state.event_id,
                    guest_id=guest.id
                ).delete()
                
                # Mark as not provided so they can re-enter
                guest.availability_provided = False
                guest.save()
                
            # Clear menu confirmation state - they're back to providing availability
            state_data = guest_state.get_state_data()
            state_data['awaiting_menu_choice'] = False
            guest_state.set_state_data(state_data)
            guest_state.save()
                
        except Exception as e:
            logger.error(f"Error clearing availability: {e}")
        
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
    
    def _handle_busy_response(self, guest_state: GuestState) -> str:
        """Handle when guest responds that they're busy/unavailable for all proposed days"""
        try:
            # Find the guest record
            guest = Guest.query.filter_by(
                event_id=guest_state.event_id,
                phone_number=guest_state.phone_number
            ).first()
            
            # If not found, try with +1 prefix format
            if not guest:
                formatted_phone = f"+1{guest_state.phone_number}"
                guest = Guest.query.filter_by(
                    event_id=guest_state.event_id,
                    phone_number=formatted_phone
                ).first()
            
            if guest:
                # Mark as having provided availability (even though they're unavailable)
                guest.availability_provided = True
                guest.save()
                
                # Send notification to planner
                self._send_busy_planner_notification(guest_state, guest)
            
            # Mark guest state for cleanup
            guest_state.current_state = 'completed'
            guest_state.save()
            
            return "Thanks for letting me know! I've notified the planner that you're not available for the proposed dates."
            
        except Exception as e:
            logger.error(f"Error handling busy response: {e}")
            return "Thanks for the response! I'll let the planner know."
    
    def _send_busy_planner_notification(self, guest_state: GuestState, guest: Guest) -> None:
        """Send notification to planner when guest is busy for all dates"""
        try:
            planner_name = guest_state.event.planner.name
            guest_name = self._extract_first_name(guest.name)
            
            # Count remaining guests who haven't responded
            total_guests = Guest.query.filter_by(event_id=guest_state.event_id).count()
            responded_guests = Guest.query.filter_by(
                event_id=guest_state.event_id, 
                availability_provided=True
            ).count()
            remaining_guests = total_guests - responded_guests
            
            # Create planner notification message
            if remaining_guests > 0:
                planner_message = f"❌ {guest_name} is not available for any of the proposed dates.\n\n"
                planner_message += f"📊 {responded_guests}/{total_guests} guests have responded\n"
                planner_message += f"⏳ Waiting for {remaining_guests} more guest" + ("s" if remaining_guests != 1 else "") + "\n\n"
                planner_message += f"Press 1 to view current overlaps"
            else:
                planner_message = f"❌ {guest_name} is not available for any of the proposed dates.\n\n"
                planner_message += f"📊 All guests have responded!\n\n"
                planner_message += "Would you like to:\n"
                planner_message += "1. Pick a time (from available guests)\n"
                planner_message += "2. Add more guests or dates"
            
            # Send SMS to planner
            planner_phone = guest_state.event.planner.phone_number
            self.sms_service.send_sms(planner_phone, planner_message)
            logger.info(f"Sent busy notification to {planner_phone} about {guest_name}'s unavailability")
            
        except Exception as e:
            logger.error(f"Error sending busy planner notification: {e}")

    def _validate_availability_entry(self, avail_data: dict) -> dict:
        """Validate a single availability entry for logical consistency"""
        try:
            date = avail_data.get('date')
            start_time = avail_data.get('start_time')
            end_time = avail_data.get('end_time')
            
            # Check required fields
            if not all([date, start_time, end_time]):
                return {
                    'valid': False,
                    'error': 'Missing date, start time, or end time'
                }
            
            # Parse times
            try:
                start_dt = datetime.strptime(start_time, '%H:%M')
                end_dt = datetime.strptime(end_time, '%H:%M')
            except ValueError:
                return {
                    'valid': False,
                    'error': f'Invalid time format: {start_time} to {end_time}'
                }
            
            # Check if start time equals end time (zero duration)
            if start_dt == end_dt:
                return {
                    'valid': False,
                    'error': f'Start and end time are the same ({start_time}). Please specify a time range.'
                }
            
            # Check if start time is after end time
            if start_dt > end_dt:
                return {
                    'valid': False,
                    'error': f'Start time ({start_time}) is after end time ({end_time})'
                }
            
            # Check for extremely short durations (less than 30 minutes)
            duration = (end_dt - start_dt).total_seconds() / 60  # minutes
            if duration < 30:
                return {
                    'valid': False,
                    'error': f'Time slot too short ({int(duration)} minutes). Minimum is 30 minutes.'
                }
            
            return {'valid': True}
            
        except Exception as e:
            logger.error(f"Error validating availability entry: {e}")
            return {
                'valid': False,
                'error': 'Could not validate time entry'
            }
    
    def _is_valid_availability_input(self, message: str, context: dict = None) -> bool:
        """Check if input matches clear availability patterns (positive matching)"""
        try:
            message_lower = message.lower().strip()
            
            # Empty or too short
            if len(message_lower) < 3:
                return False
            
            import re
            
            # Check if this is a single-day event
            is_single_day = False
            if context and context.get('event_dates'):
                is_single_day = len(context['event_dates']) == 1
            
            # Define clear patterns we DO accept
            valid_patterns = [
                # Day + time period: "monday morning", "saturday afternoon"
                r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(morning|afternoon|evening|night)\b',
                
                # Day + "all day": "saturday all day", "monday allday"
                r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(all\s*day)\b',
                
                # Day + specific time: "monday 2pm", "saturday 6am", "friday 10:30am", "friday 7p"
                r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+\d{1,2}(:\d{2})?\s*(am?|pm?)\b',
                
                # Day + time range with AM/PM: "monday 2-6pm", "saturday 9am-5pm", "friday 2pm to 8pm", "friday 7-11p"
                r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+\d{1,2}(:\d{2})?\s*(am?|pm?)?\s*(-|to)\s*\d{1,2}(:\d{2})?\s*(am?|pm?)\b',
                
                # Day + time range without AM/PM: "friday 2-4", "monday 9-5"
                r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+\d{1,2}\s*-\s*\d{1,2}\b',
                
                # Day + "from" + time range: "friday from 2-4", "monday from 9am-5pm"
                r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+from\s+\d{1,2}(:\d{2})?\s*(am|pm)?\s*(-|to)\s*\d{1,2}(:\d{2})?\s*(am|pm)?\b',
                
                # Day + "after/before time": "monday after 2pm", "saturday before 6pm", "friday after 7p"
                r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|mon|tue|wed|thu|fri|sat|sun)\s+(after|before)\s+\d{1,2}(:\d{2})?\s*(am?|pm?)\b',
                
                # Just time periods: "morning", "afternoon", "evening", "all day" (always allowed)
                r'^\s*(morning|afternoon|evening|night|all\s*day)\s*$'
            ]
            
            # For single-day events, also accept time-only patterns
            if is_single_day:
                time_only_patterns = [
                    # Simple time ranges: "2-4", "2-4pm", "from 2-4", "from 2-4pm", "7-11p"
                    r'^\s*(from\s+)?\d{1,2}(:\d{2})?\s*(-|to)\s*\d{1,2}(:\d{2})?\s*(am?|pm?)?\s*$',
                    
                    # Time with AM/PM: "2pm", "11am", "2:30pm", "7p"
                    r'^\s*\d{1,2}(:\d{2})?\s*(am?|pm?)\s*$',
                    
                    # After/before times: "after 2pm", "before 6pm", "after 7p"
                    r'^\s*(after|before)\s+\d{1,2}(:\d{2})?\s*(am?|pm?)\s*$',
                    
                    # Simple number ranges: "2-4", "9-5" (without am/pm)
                    r'^\s*\d{1,2}\s*-\s*\d{1,2}\s*$'
                ]
                valid_patterns.extend(time_only_patterns)
            else:
                # For multi-day events, only accept time ranges with AM/PM specified
                multi_day_time_patterns = [
                    # Time ranges with clear AM/PM: "2-6pm", "9am-5pm", "2pm-6pm", "7-11p"
                    r'^\s*\d{1,2}(:\d{2})?\s*(am?|pm?)?\s*(-|to)\s*\d{1,2}(:\d{2})?\s*(am?|pm?)\s*$',
                    
                    # After/before times: "after 2pm", "before 6pm", "after 7p"
                    r'^\s*(after|before)\s+\d{1,2}(:\d{2})?\s*(am?|pm?)\s*$'
                ]
                valid_patterns.extend(multi_day_time_patterns)
            
            # Check if message matches any valid pattern
            for pattern in valid_patterns:
                if re.search(pattern, message_lower):
                    if is_single_day and pattern in time_only_patterns:
                        logger.info(f"Input validation for '{message}': VALID - matched single-day time pattern: {pattern}")
                    else:
                        logger.info(f"Input validation for '{message}': VALID - matched pattern: {pattern}")
                    return True
            
            # If no patterns matched, it's not a valid availability input
            logger.info(f"Input validation for '{message}': INVALID - no patterns matched (single_day: {is_single_day})")
            return False
            
        except Exception as e:
            logger.error(f"Error validating availability input: {e}")
            return False
    
    # NEW METHODS FOR PREFERENCES WORKFLOW
    
    def _handle_confirm_availability(self, guest_state: GuestState) -> str:
        """Handle availability confirmation - transition to preferences request"""
        try:
            # Send preferences request
            guest_name = self._get_guest_name(guest_state)
            
            message = f"✅Confirmed! Do you have any activity preferences?\n\n"
            message += "Examples:\n"
            message += "- \"Let's do something outdoors\"\n"
            message += "- \"Drinks\"\n"
            message += "- \"Italian food\"\n"
            message += "- \"None\"\n\n"
            message += "Just reply with your thoughts! 💭"
            
            # Update state
            guest_state.current_state = 'awaiting_preferences'
            state_data = guest_state.get_state_data()
            state_data['awaiting_menu_choice'] = False
            guest_state.set_state_data(state_data)
            guest_state.save()
            
            return message
            
        except Exception as e:
            logger.error(f"Error handling availability confirmation: {e}")
            return "Sorry, something went wrong. Please try again."
    
    def _handle_preferences_response(self, guest_state: GuestState, message: str) -> str:
        """Handle guest preferences response"""
        try:
            # Get the guest record and save preferences
            guest = self._get_guest_record(guest_state)
            if not guest:
                logger.error(f"Could not find guest record for state: {guest_state.phone_number}")
                return "Sorry, something went wrong. Please try again."
                
            # Save preferences
            guest.preferences = message.strip()
            guest.preferences_provided = True
            guest.save()
            logger.info(f"Saved preferences for guest {guest.name}: {guest.preferences}")
            
            # Get availability data from state for final confirmation
            state_data = guest_state.get_state_data()
            availability_data = state_data.get('availability_data', [])
            
            if not availability_data:
                logger.error(f"No availability data found in guest state for {guest_state.phone_number}")
                return "Sorry, I couldn't find your availability information. Please start over."
            
            # Format final confirmation
            response_text = "Got it! Let me confirm everything:\n\n"
            response_text += "📅 Your availability:\n\n"
            for avail_data in availability_data:
                try:
                    date_obj = datetime.strptime(avail_data['date'], '%Y-%m-%d').date()
                    day_name = date_obj.strftime('%A')
                    start_time = self._format_time_12hr(avail_data['start_time'])
                    end_time = self._format_time_12hr(avail_data['end_time'])
                    response_text += f"- {day_name} {start_time}-{end_time}\n"
                except Exception as e:
                    logger.error(f"Error formatting availability data: {e}")
                    response_text += f"- {avail_data.get('date', 'Unknown date')}\n"
            
            response_text += f"\nActivity preference: {message.strip()}\n\n"
            response_text += "Is this all correct?\n\n"
            response_text += "1. Yes, send to planner\n"
            response_text += "2. Change my availability\n" 
            response_text += "3 Change my preferences"
            
            # Update state for final confirmation
            state_data['awaiting_final_choice'] = True
            state_data['awaiting_menu_choice'] = False  # Clear old menu state
            guest_state.set_state_data(state_data)
            guest_state.save()
            logger.info(f"Updated guest state to awaiting_final_choice for {guest_state.phone_number}")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error handling preferences response: {e}", exc_info=True)
            return "Sorry, something went wrong. Please try again."
    
    def _handle_send_final_availability(self, guest_state: GuestState) -> str:
        """Send final availability to planner with preferences"""
        try:
            # Get the guest record
            guest = self._get_guest_record(guest_state)
            if guest:
                # Mark as complete
                guest.availability_provided = True
                guest.preferences_provided = True
                guest.save()
                
                # Send planner notification
                self._send_enhanced_planner_notification(guest_state, guest)
                
                # Mark guest state for cleanup
                guest_state.current_state = 'completed'
                guest_state.save()
                
                # Safely get planner name
                try:
                    event = guest_state.event
                    planner_name = event.planner.name if event and event.planner and event.planner.name else "your planner"
                except Exception:
                    planner_name = "your planner"
                
                return f"Perfect! Thanks for sharing your availability and preferences. {planner_name} will use this to plan something great! 🎯"
            
            return "Thanks! Your information has been sent."
            
        except Exception as e:
            logger.error(f"Error sending final availability: {e}")
            return "Thanks! Your information has been sent."
    
    def _handle_change_availability_final(self, guest_state: GuestState) -> str:
        """Handle changing availability from final confirmation"""
        try:
            # Reset to availability input state
            guest_state.current_state = 'awaiting_availability'
            state_data = guest_state.get_state_data()
            state_data['awaiting_menu_choice'] = False
            state_data['awaiting_final_choice'] = False
            guest_state.set_state_data(state_data)
            guest_state.save()
            
            return "No problem! Please provide your updated availability:"
            
        except Exception as e:
            logger.error(f"Error handling availability change: {e}")
            return "No problem! Please provide your updated availability:"
    
    def _handle_change_preferences(self, guest_state: GuestState) -> str:
        """Handle changing preferences from final confirmation"""
        try:
            # Reset to preferences state
            guest_state.current_state = 'awaiting_preferences'
            state_data = guest_state.get_state_data()
            state_data['awaiting_final_choice'] = False
            guest_state.set_state_data(state_data)
            guest_state.save()
            
            message = "No problem! What are your preferences for the hangout?\n\n"
            message += "Examples:\n"
            message += "- \"Let's do something outdoors\"\n"
            message += "- \"Drinks\"\n"
            message += "- \"Italian food\"\n"
            message += "- \"None\"\n\n"
            message += "Just reply with your thoughts! 💭"
            
            return message
            
        except Exception as e:
            logger.error(f"Error handling preferences change: {e}")
            return "No problem! What are your preferences for the hangout?"
    
    def _get_guest_record(self, guest_state: GuestState) -> Guest:
        """Get guest record with phone number format handling"""
        guest = Guest.query.filter_by(
            event_id=guest_state.event_id,
            phone_number=guest_state.phone_number
        ).first()
        
        # If not found, try with +1 prefix format
        if not guest:
            formatted_phone = f"+1{guest_state.phone_number}"
            guest = Guest.query.filter_by(
                event_id=guest_state.event_id,
                phone_number=formatted_phone
            ).first()
        
        return guest
    
    def _get_guest_name(self, guest_state: GuestState) -> str:
        """Get guest first name"""
        guest = self._get_guest_record(guest_state)
        return self._extract_first_name(guest.name) if guest else "Friend"
    
    def _send_enhanced_planner_notification(self, guest_state: GuestState, guest: Guest) -> None:
        """Send enhanced planner notification with preferences"""
        try:
            planner_name = guest_state.event.planner.name
            guest_name = self._extract_first_name(guest.name)
            
            # Get guest's availability details
            availability_details = self._format_guest_availability_details(guest)
            
            # Count remaining guests who haven't responded
            total_guests = Guest.query.filter_by(event_id=guest_state.event_id).count()
            responded_guests = Guest.query.filter_by(
                event_id=guest_state.event_id, 
                availability_provided=True
            ).count()
            remaining_guests = total_guests - responded_guests
            
            # Create enhanced planner notification message
            planner_message = f"✅ {guest_name} has provided their availability:\n\n{availability_details}\n"
            
            # Add preferences
            if guest.preferences:
                planner_message += f"\n💭 Preferences: \"{guest.preferences}\"\n"
            else:
                planner_message += f"\n💭 Preferences: No specific preferences\n"
            
            if remaining_guests > 0:
                planner_message += f"\n📊 {responded_guests}/{total_guests} guests have responded\n"
                planner_message += f"⏳ Waiting for {remaining_guests} more guest" + ("s" if remaining_guests != 1 else "") + "\n\n"
                planner_message += f"Press 1 to view current overlaps"
            else:
                planner_message += f"\n🎉 Everyone has responded!\n\n"
                planner_message += "Would you like to:\n"
                planner_message += "1. Pick a time\n"
                planner_message += "2. Add more guests"
            
            # Send SMS to planner
            planner_phone = guest_state.event.planner.phone_number
            self.sms_service.send_sms(planner_phone, planner_message)
            logger.info(f"Sent enhanced planner notification to {planner_phone} about {guest_name}'s availability and preferences")
            
        except Exception as e:
            logger.error(f"Error sending enhanced planner notification: {e}")
            
        except Exception as e:
            logger.error(f"Error validating input: {e}")
            return False  # If validation fails, reject the input
