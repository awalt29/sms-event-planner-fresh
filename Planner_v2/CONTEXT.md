# Complete SMS Event Planner Rebuild - Comprehensive Context Document

## Application Overview

A sophisticated SMS-based event planning application that manages complex conversational workflows entirely through text messages. The system handles dual user roles (planners and guests) with seamless state transitions, natural language processing, AI-powered venue suggestions, and intelligent coordination workflows.

## Visual Flow Documentation (From Screenshots)

### Complete Planner Journey
1. **Welcome & Setup**: "🎉 Welcome to Gatherly! What's your name?" → Name collection
2. **Guest Collection**: Contact-based guest addition with phone number validation and previous contact selection
3. **Date Planning**: Natural language date input ("Monday") with confirmation menus showing 3 options
4. **Availability Coordination**: Automated guest notification with real-time status tracking
5. **Time Selection**: AI-powered overlap calculation with numbered options and attendance percentages
6. **Location Input**: Geographic location collection with examples
7. **Activity Description**: Activity type input with intelligent AI parsing
8. **Venue Selection**: AI-powered suggestions with Google Maps integration and fallback options
9. **Final Confirmation**: Complete event summary with invitation distribution
10. **RSVP Tracking**: Real-time guest response notifications with status updates

### Complete Guest Journey
1. **Availability Request**: "Hi Awork! Aaron wants to hang out on one of these days: - Monday, August 4"
2. **Natural Language Response**: "Monday after 2pm" → AI parsing and interpretation
3. **Confirmation Process**: "Got it! Here's your availability: - Mon, 8/4: 2:00pm to 11:59pm" with 1/2 options
4. **State Management**: "✅ Thanks! I've recorded your availability. Aaron will use this to find the best time for everyone."
5. **Final Invitation**: Complete event details with venue links and planner attribution
6. **RSVP Process**: "🎉 You're invited! Please reply 'Yes', 'No', or 'Maybe' to confirm your attendance!"
7. **Confirmation**: "🎉 Great! You're confirmed for the event." → Automatic return to planner mode

## Message Formatting Standards (Exact from Screenshots)

### Event Ready Summary
```
🎉 Event Ready to Send!

📅 Date: Monday, August 4
🕒 Time: 02:00pm-11:59pm
🏢 Activity: Starbucks
👥 Attendees: Awork

Would you like to:
1. Send invitations to guests
Or reply 'restart' to start over with a new event
```

### Guest Availability Request
```
Hi Awork! Aaron wants to hang out on one of these days:

- Monday, August 4

Reply with your availability. You can say things like:

- 'Friday 2-6pm, Saturday after 4pm'
- 'Friday all day, Saturday evening'
- 'Friday after 3pm'
```

### Venue Suggestions Format
```
🎯 Perfect! Looking for Coffee in Manhattan.

Here are some great options:

1. Starbucks
https://www.google.com/maps/search/Starbucks+Manhattan+Coffee
- Global coffee chain

2. Blue Bottle Coffee
https://www.google.com/maps/search/Blue+Bottle+Coffee+Manhattan+Coffee
- Hip artisanal coffee shop

3. Stumptown Coffee Roasters
https://www.google.com/maps/search/Stumptown+Coffee+Roasters+Manhattan+Coffee
- Specialty coffee roastery

Select an option (1,2,3) or say:
- 'New list' for more options
- 'Activity' to change the activity
- 'Location' to change the location
```

### Availability Status Tracking
```
📊 Availability Status:

✅ Responded: 1/1
⏳ Pending: 0

🎉 Everyone has responded!

Would you like to:
1. Pick a time
2. Add more guests
```

### Time Selection with Overlaps
```
🕒 Best available timeslots:

1. Mon, 8/4: 2:00pm-11:59pm
Attendance: 100%
Available: Awork

Reply with the number of your preferred(e.g. 1,2,3)
```

### Final Guest Invitation
```
🎉 You're invited!

📅 Date: Monday, August 4
🕒 Time: 02:00pm-11:59pm
🏢 Venue: Starbucks
https://www.google.com/maps/search/Starbucks+Manhattan+Coffee

Planned by: Aaron

Please reply 'Yes', 'No', or 'Maybe' to confirm your attendance!
```

## Critical Architecture Pattern: Everyone is a Planner by Default

### The Simple Approach
**Everyone is treated as a planner unless they have an active guest state from receiving a specific guest message (availability request or invitation).**

### The Solution
**Default Planner Mode with Temporary Guest Override**

1. **Planner is Default**: All users are planners by default - no special setup needed
2. **Guest State Only for Responses**: `GuestState` records are created only when sending availability/RSVP requests
3. **Automatic Return**: After guest workflows complete, users automatically return to planner mode
4. **Clean State Management**: No complex role switching - just temporary guest overrides

### Implementation Pattern
```python
def route_message(self, phone_number: str, message: str) -> str:
    # Check if they're temporarily in guest mode (responding to an invitation)
    guest_state = GuestState.query.filter_by(phone_number=normalized_phone).first()
    
    if guest_state:
        # Handle as guest (temporary override)
        response = self._handle_guest_message(guest_state, message)
        
        # Check if guest workflow is complete
        if self._is_guest_workflow_complete(guest_state, message):
            self._cleanup_guest_state(guest_state)  # Return to default planner mode
        
        return response
    
    # Default: Handle as planner (no special setup needed)
    planner = self._get_or_create_planner(normalized_phone)
    return self._handle_planner_message(planner, message)
```

### Workflow Examples
- **User A** texts "Plan dinner Friday" → automatically becomes planner, creates event
- **User A** invites **User B** → system creates `GuestState` for **User B**
- **User B** receives availability request → temporarily handles as guest
- **User B** responds "Friday 7pm works" → availability saved, guest state deleted, **User B** returns to planner mode
- **User B** next message → automatically handled as planner (can create own events immediately)
- **Later**: **User A** sends RSVP request → creates new `GuestState` for **User B**
- **User B** responds "Yes" → RSVP saved, guest state deleted, **User B** returns to planner mode

### Guest State Lifecycle (Per-Message Cleanup)
1. **Creation**: Only when receiving availability/RSVP requests from other planners
2. **Active**: During single message response (not entire workflow)
3. **Cleanup**: After EACH individual response message (availability OR RSVP)
4. **Return**: Immediate return to default planner mode after each guest response

## Database Architecture

### Core Models with Relationships
```python
from sqlalchemy import Column, Integer, String, DateTime, Date, Time, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import json

Base = declarative_base()

class BaseModel(Base):
    """Base model with common fields and methods"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def save(self):
        """Save instance to database"""
        from app import db
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        """Delete instance from database"""
        from app import db
        db.session.delete(self)
        db.session.commit()
    
    def to_dict(self):
        """Convert instance to dictionary"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

class Planner(BaseModel):
    """Event planners who organize hangouts"""
    __tablename__ = 'planners'
    
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    
    # Relationships
    events = relationship("Event", back_populates="planner", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="planner", cascade="all, delete-orphan")

class Event(BaseModel):
    """Events being planned"""
    __tablename__ = 'events'
    
    # Foreign keys
    planner_id = Column(Integer, ForeignKey('planners.id'), nullable=False)
    
    # Event details
    title = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)
    activity = Column(String(200), nullable=True)
    start_date = Column(Date, nullable=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    
    # Workflow management
    workflow_stage = Column(String(50), nullable=False, default='collecting_guests')
    status = Column(String(20), nullable=False, default='planning')
    
    # Venue management
    venue_suggestions = Column(JSON, nullable=True)
    selected_venue = Column(JSON, nullable=True)
    
    # Notes and workflow data
    notes = Column(Text, nullable=True)
    
    # Relationships
    planner = relationship("Planner", back_populates="events")
    guests = relationship("Guest", back_populates="event", cascade="all, delete-orphan")
    guest_states = relationship("GuestState", back_populates="event", cascade="all, delete-orphan")

class Guest(BaseModel):
    """Event attendees"""
    __tablename__ = 'guests'
    
    # Foreign keys
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=True)
    
    # Guest details
    name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    
    # RSVP tracking
    rsvp_status = Column(String(20), nullable=False, default='pending')
    availability_provided = Column(Boolean, nullable=False, default=False)
    
    # Relationships
    event = relationship("Event", back_populates="guests")
    contact = relationship("Contact", back_populates="guests")
    availability_records = relationship("Availability", back_populates="guest", cascade="all, delete-orphan")

class GuestState(BaseModel):
    """Temporary conversation states for non-planners"""
    __tablename__ = 'guest_states'
    
    # Foreign keys
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    
    # State management
    phone_number = Column(String(20), nullable=False, unique=True, index=True)
    current_state = Column(String(50), nullable=False)
    state_data = Column(JSON, nullable=True)
    
    # Relationships
    event = relationship("Event", back_populates="guest_states")
    
    def set_state_data(self, data):
        """Helper to set state data"""
        self.state_data = json.dumps(data) if data else None
    
    def get_state_data(self):
        """Helper to get state data"""
        return json.loads(self.state_data) if self.state_data else {}

class Contact(BaseModel):
    """Planner's saved contacts"""
    __tablename__ = 'contacts'
    
    # Foreign keys
    planner_id = Column(Integer, ForeignKey('planners.id'), nullable=False)
    
    # Contact details
    name = Column(String(100), nullable=False)
    phone_number = Column(String(20), nullable=False)
    last_contacted = Column(DateTime, nullable=True)
    
    # Relationships
    planner = relationship("Planner", back_populates="contacts")
    guests = relationship("Guest", back_populates="contact")

class Availability(BaseModel):
    """Guest availability data"""
    __tablename__ = 'availability'
    
    # Foreign keys
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False)
    guest_id = Column(Integer, ForeignKey('guests.id'), nullable=False)
    
    # Availability details
    date = Column(Date, nullable=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)
    all_day = Column(Boolean, nullable=False, default=False)
    preference_level = Column(String(20), nullable=False, default='available')
    notes = Column(Text, nullable=True)
    
    # Relationships
    guest = relationship("Guest", back_populates="availability_records")
```

## Service Layer Architecture

### Event Workflow Service
```python
from typing import Dict, List, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)

class EventWorkflowService:
    """Manages event planning workflow and state transitions"""
    
    def __init__(self):
        self.message_formatter = MessageFormattingService()
        self.ai_service = AIProcessingService()
    
    def create_event_from_text(self, planner_id: int, text: str) -> Dict:
        """Create new event from natural language description"""
        try:
            # Parse event details using AI
            parsed_event = self.ai_service.parse_event_input(text)
            
            # Create event record
            event = Event(
                planner_id=planner_id,
                title=parsed_event.get('title'),
                location=parsed_event.get('location'),
                activity=parsed_event.get('activity'),
                workflow_stage='collecting_guests',
                status='planning'
            )
            event.save()
            
            return {'success': True, 'event': event}
            
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return {'success': False, 'error': str(e)}
    
    def transition_to_stage(self, event: Event, new_stage: str) -> bool:
        """Validate and execute workflow state transition"""
        valid_transitions = self._get_valid_transitions(event.workflow_stage)
        
        if new_stage in valid_transitions:
            event.workflow_stage = new_stage
            event.save()
            return True
        
        logger.warning(f"Invalid transition from {event.workflow_stage} to {new_stage}")
        return False
    
    def _get_valid_transitions(self, current_stage: str) -> List[str]:
        """Get valid next stages for current workflow stage"""
        transitions = {
            'collecting_guests': ['collecting_dates', 'removing_contacts'],
            'collecting_dates': ['awaiting_confirmation'],
            'awaiting_confirmation': ['collecting_availability', 'collecting_dates', 'collecting_guests'],
            'collecting_availability': ['selecting_time', 'collecting_guests'],
            'selecting_time': ['collecting_location'],
            'collecting_location': ['collecting_activity'],
            'collecting_activity': ['selecting_venue'],
            'selecting_venue': ['final_confirmation', 'collecting_activity', 'collecting_location'],
            'final_confirmation': ['finalized']
        }
        return transitions.get(current_stage, [])

class GuestManagementService:
    """Manages guest addition, availability, and RSVP tracking"""
    
    def __init__(self):
        self.sms_service = SMSService()
        self.ai_service = AIProcessingService()
    
    def add_guests_from_text(self, event_id: int, text: str) -> Dict:
        """Parse guest information from text and add to event"""
        try:
            # Parse guest info using AI or regex patterns
            parsed_guests = self._parse_guest_text(text)
            
            if not parsed_guests:
                return {'success': False, 'error': 'Could not parse guest information'}
            
            added_guests = []
            for guest_data in parsed_guests:
                # Check for existing guest
                existing = Guest.query.filter_by(
                    event_id=event_id,
                    phone_number=guest_data['phone_number']
                ).first()
                
                if not existing:
                    guest = Guest(
                        event_id=event_id,
                        name=guest_data['name'],
                        phone_number=guest_data['phone_number'],
                        rsvp_status='pending',
                        availability_provided=False
                    )
                    guest.save()
                    added_guests.append(guest)
                    
                    # Save as contact for future use
                    self._save_as_contact(event_id, guest_data)
            
            return {'success': True, 'guests': added_guests}
            
        except Exception as e:
            logger.error(f"Error adding guests: {e}")
            return {'success': False, 'error': str(e)}
    
    def send_availability_request(self, guest: Guest) -> bool:
        """Send availability request to guest"""
        try:
            event = guest.event
            planner = event.planner
            
            # Format availability request message
            message = self._format_availability_request(guest, event, planner)
            
            # Send SMS
            success = self.sms_service.send_sms(guest.phone_number, message)
            
            if success:
                # Create guest state for tracking response
                guest_state = GuestState(
                    phone_number=guest.phone_number,
                    event_id=event.id,
                    current_state='awaiting_availability'
                )
                guest_state.save()
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending availability request: {e}")
            return False
    
    def _parse_guest_text(self, text: str) -> List[Dict]:
        """Parse guest information from text input"""
        # Implementation for parsing "John Doe, 123-456-7890" format
        import re
        
        # Pattern for name and phone number
        pattern = r'([^,]+),\s*([0-9\-\(\)\s]+)'
        matches = re.findall(pattern, text)
        
        guests = []
        for name, phone in matches:
            normalized_phone = self._normalize_phone(phone.strip())
            if normalized_phone:
                guests.append({
                    'name': name.strip(),
                    'phone_number': normalized_phone
                })
        
        return guests
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to standard format"""
        # Remove all non-digits
        digits = ''.join(filter(str.isdigit, phone))
        
        # Handle different formats
        if len(digits) == 10:
            return digits
        elif len(digits) == 11 and digits.startswith('1'):
            return digits[1:]
        
        return None

    def _format_availability_request(self, guest: Guest, event: Event, planner: Planner) -> str:
        """Format availability request message for guest"""
        # Parse dates from event notes
        dates_text = "the proposed dates"
        if event.notes and "Proposed dates:" in event.notes:
            dates_text = event.notes.split("Proposed dates: ")[1].split("\n")[0]
        
        message = f"Hi {guest.name}! {planner.name} wants to hang out on one of these days:\n\n"
        message += f"- {dates_text}\n\n"
        message += "Reply with your availability. You can say things like:\n\n"
        message += "- 'Friday 2-6pm, Saturday after 4pm'\n"
        message += "- 'Friday all day, Saturday evening'\n"
        message += "- 'Friday after 3pm'"
        
        return message

class MessageFormattingService:
    """Handles all message formatting with consistent emoji usage"""
    
    def format_planner_confirmation_menu(self, event: Event) -> str:
        """Generate 3-option confirmation menu"""
        guest_list = "\n".join([f"- {guest.name} ({guest.phone_number})" for guest in event.guests])
        
        response_text = "Got it, planning for:\n"
        if event.notes and "Proposed dates:" in event.notes:
            dates_text = event.notes.split("Proposed dates: ")[1].split("\n")[0]
            response_text += f"- {dates_text}\n"
        
        response_text += f"\nGuest list:\n{guest_list}\n\n"
        response_text += "Would you like to:\n"
        response_text += "1. Request guest availability\n"
        response_text += "2. Change the dates\n"
        response_text += "3. Add more guests\n\n"
        response_text += "Reply with 1, 2, or 3."
        
        return response_text
    
    def format_availability_status(self, event: Event) -> str:
        """Create availability tracking summary"""
        total_guests = len(event.guests)
        provided_count = sum(1 for guest in event.guests if guest.availability_provided)
        pending_count = total_guests - provided_count
        
        status_text = f"📊 Availability Status:\n\n"
        status_text += f"✅ Responded: {provided_count}/{total_guests}\n"
        status_text += f"⏳ Pending: {pending_count}\n\n"
        
        if pending_count > 0:
            pending_guests = [guest for guest in event.guests if not guest.availability_provided]
            status_text += "Still waiting for:\n"
            for guest in pending_guests:
                status_text += f"- {guest.name}\n"
            status_text += "\nSend 'remind' to send follow-up messages."
        else:
            status_text += "🎉 Everyone has responded!\n\n"
            status_text += "Would you like to:\n"
            status_text += "1. Pick a time\n"
            status_text += "2. Add more guests"
        
        return status_text
    
    def format_venue_suggestions(self, venues: List[Dict], activity: str, location: str) -> str:
        """Format venue options with Google Maps links"""
        response_text = f"🎯 Perfect! Looking for {activity} in {location}.\n\n"
        response_text += "Here are some great options:\n\n"
        
        for i, venue in enumerate(venues, 1):
            response_text += f"{i}. {venue.get('name', 'Unknown venue')}\n"
            response_text += f"{venue.get('link', '')}\n"
            if venue.get('description'):
                response_text += f"- {venue['description']}\n\n"
            else:
                response_text += "\n"
        
        response_text += "Select an option (1,2,3) or say:\n"
        response_text += "- 'New list' for more options\n"
        response_text += "- 'Activity' to change the activity\n"
        response_text += "- 'Location' to change the location"
        
        return response_text
    
    def format_guest_invitation(self, event: Event, guest: Guest) -> str:
        """Create final invitation message"""
        # Format date and time
        date_obj = event.start_date
        formatted_date = date_obj.strftime('%A, %B %-d') if date_obj else "TBD"
        
        if event.start_time and event.end_time:
            start_time = event.start_time.strftime('%I:%M%p').lower()
            end_time = event.end_time.strftime('%I:%M%p').lower()
            time_str = f"{start_time}-{end_time}"
        else:
            time_str = "All day"
        
        # Get venue details
        venue_info = "Selected venue"
        venue_link = ""
        if event.selected_venue:
            try:
                import json
                venue_data = json.loads(event.selected_venue)
                venue_info = venue_data.get('name', 'Selected venue')
                venue_link = venue_data.get('link', '')
            except:
                pass
        
        invitation_msg = f"🎉 You're invited!\n\n"
        invitation_msg += f"📅 Date: {formatted_date}\n"
        invitation_msg += f"🕒 Time: {time_str}\n"
        invitation_msg += f"🏢 Venue: {venue_info}\n"
        if venue_link:
            invitation_msg += f"{venue_link}\n"
        invitation_msg += f"\nPlanned by: {event.planner.name or 'Your event planner'}\n\n"
        invitation_msg += "Please reply 'Yes', 'No', or 'Maybe' to confirm your attendance!"
        
        return invitation_msg

class AIProcessingService:
    """Handles AI integration for natural language processing"""
    
    def __init__(self):
        from openai import OpenAI
        import os
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def parse_natural_language_dates(self, message: str) -> Dict:
        """Convert natural language to structured date objects"""
        try:
            prompt = f"""
            Parse the following date text into structured data:
            "{message}"
            
            Return JSON with:
            - success: boolean
            - dates: list of date strings in YYYY-MM-DD format
            - dates_text: human readable summary
            
            Examples:
            "Monday" -> {{"success": true, "dates": ["2024-08-04"], "dates_text": "Monday, August 4"}}
            "Saturday and Sunday" -> {{"success": true, "dates": ["2024-08-03", "2024-08-04"], "dates_text": "Saturday and Sunday"}}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                timeout=20
            )
            
            import json
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"AI date parsing error: {e}")
            return {'success': False, 'error': str(e)}
    
    def parse_availability_text(self, message: str, context: Dict) -> Dict:
        """Parse availability responses like 'Monday after 2pm'"""
        try:
            prompt = f"""
            Parse availability from: "{message}"
            Context: {context}
            
            Return JSON with:
            - available_dates: list of {{date, start_time, end_time, all_day}}
            - notes: any additional notes
            
            Example:
            "Monday after 2pm" -> {{
                "available_dates": [{{
                    "date": "2024-08-04",
                    "start_time": "14:00",
                    "end_time": "23:59",
                    "all_day": false
                }}]
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                timeout=20
            )
            
            import json
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"AI availability parsing error: {e}")
            return {'error': str(e)}

    def parse_event_input(self, text: str) -> Dict:
        """Parse event creation text"""
        try:
            prompt = f"""
            Parse event details from: "{text}"
            
            Return JSON with:
            - title: event title (optional)
            - location: location if mentioned
            - activity: activity type if mentioned
            - success: boolean
            
            Example:
            "dinner friday in brooklyn" -> {{
                "title": "Dinner",
                "location": "Brooklyn", 
                "activity": "dinner",
                "success": true
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                timeout=20
            )
            
            import json
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"AI event parsing error: {e}")
            return {'success': False, 'error': str(e)}

class VenueService:
    """Handles venue suggestions with AI and fallback options"""
    
    def __init__(self):
        self.ai_service = AIProcessingService()
    
    def suggest_venues(self, activity: str, location: str, requirements: List[str] = None) -> Dict:
        """Generate venue suggestions with Google Maps integration"""
        try:
            # Convert food terms intelligently
            processed_activity = self._convert_food_terms(activity)
            
            # Try AI-powered suggestions first
            ai_result = self._get_ai_venue_suggestions(processed_activity, location, requirements)
            
            if ai_result.get('success'):
                return ai_result
            
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
    
    def _get_curated_venue_suggestions(self, activity: str, location: str) -> Dict:
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
        
        return {'success': True, 'venues': venues, 'method': 'curated'}

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

class SMSService:
    """Handles SMS communication via Twilio"""
    
    def __init__(self):
        from twilio.rest import Client
        import os
        self.client = Client(os.getenv('TWILIO_SID'), os.getenv('TWILIO_AUTH'))
        self.from_number = os.getenv('TWILIO_NUMBER')
    
    def send_sms(self, to_number: str, message: str) -> bool:
        """Send SMS message"""
        try:
            message = self.client.messages.create(
                body=message,
                from_=self.from_number,
                to=f"+1{to_number}"
            )
            return True
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return False
```

## Handler Pattern Implementation

### Base Handler Class
```python
from abc import ABC, abstractmethod
from typing import Dict, Optional
from dataclasses import dataclass

@dataclass
class HandlerResult:
    """Result object for handler operations"""
    success: bool
    message: str
    next_stage: Optional[str] = None
    error_code: Optional[str] = None
    
    @classmethod
    def success_response(cls, message: str, next_stage: str = None) -> 'HandlerResult':
        return cls(success=True, message=message, next_stage=next_stage)
    
    @classmethod
    def error_response(cls, message: str, error_code: str = None) -> 'HandlerResult':
        return cls(success=False, message=message, error_code=error_code)
    
    @classmethod
    def transition_to(cls, stage: str) -> 'HandlerResult':
        return cls(success=True, message="", next_stage=stage)

class BaseWorkflowHandler(ABC):
    """Base class for all workflow stage handlers"""
    
    def __init__(self, event_service: EventWorkflowService, 
                 guest_service: GuestManagementService,
                 message_service: MessageFormattingService,
                 ai_service: AIProcessingService):
        self.event_service = event_service
        self.guest_service = guest_service
        self.message_service = message_service
        self.ai_service = ai_service
    
    @abstractmethod
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        """Process message for this workflow stage"""
        pass
    
    def validate_input(self, message: str, context: Dict) -> bool:
        """Validate input for this stage"""
        return len(message.strip()) > 0

class GuestCollectionHandler(BaseWorkflowHandler):
    """Handles guest collection workflow stage"""
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            message_lower = message.lower().strip()
            
            # Handle special commands
            if message_lower in ['done', 'finished', 'next']:
                if len(event.guests) == 0:
                    return HandlerResult.error_response(
                        "You haven't added any guests yet. Please add at least one guest before proceeding."
                    )
                return HandlerResult.transition_to('collecting_dates')
            
            # Handle contact selection (numeric input)
            if message.strip().isdigit() or ',' in message.strip():
                return self._handle_contact_selection(event, message)
            
            # Handle new guest addition
            result = self.guest_service.add_guests_from_text(event.id, message)
            
            if result['success']:
                guest = result['guests'][0]
                response_msg = f"Added: {guest.name} ({guest.phone_number})\n\n"
                response_msg += "Add more guests, or reply 'done' when finished."
                return HandlerResult.success_response(response_msg)
            else:
                return HandlerResult.error_response(f"❌ {result['error']}")
                
        except Exception as e:
            logger.error(f"Error in guest collection: {e}")
            return HandlerResult.error_response("Sorry, there was an error. Please try again.")
    
    def _handle_contact_selection(self, event: Event, message: str) -> HandlerResult:
        """Handle selection from previous contacts"""
        try:
            # Parse contact numbers
            if ',' in message.strip():
                selected_numbers = [int(num.strip()) for num in message.split(',')]
            else:
                selected_numbers = [int(message.strip())]
            
            # Get planner's contacts
            contacts = Contact.query.filter_by(planner_id=event.planner_id).order_by(Contact.name).all()
            
            if not contacts:
                return HandlerResult.error_response(
                    "You don't have any saved contacts yet. Please add guests with their phone numbers."
                )
            
            # Add selected contacts as guests
            added_guests = []
            for num in selected_numbers:
                if 1 <= num <= len(contacts):
                    contact = contacts[num - 1]
                    
                    # Check if already added
                    existing = Guest.query.filter_by(
                        event_id=event.id,
                        phone_number=contact.phone_number
                    ).first()
                    
                    if not existing:
                        guest = Guest(
                            event_id=event.id,
                            contact_id=contact.id,
                            name=contact.name,
                            phone_number=contact.phone_number,
                            rsvp_status='pending',
                            availability_provided=False
                        )
                        guest.save()
                        added_guests.append(guest)
            
            if added_guests:
                guest_names = [guest.name for guest in added_guests]
                response_msg = f"Added from contacts: {', '.join(guest_names)}\n\n"
                response_msg += "Add more guests or reply 'done' when finished."
                return HandlerResult.success_response(response_msg)
            else:
                return HandlerResult.error_response(
                    "Those contacts are already added or invalid numbers."
                )
                
        except ValueError:
            return HandlerResult.error_response(
                "Please use contact numbers (e.g. '1,3') or add new guests with names and phone numbers."
            )

class DateCollectionHandler(BaseWorkflowHandler):
    """Handles date collection workflow stage"""
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            # Parse dates using AI
            parsed_dates = self.ai_service.parse_natural_language_dates(message)
            
            if parsed_dates.get('success'):
                # Save dates to event
                event.notes = f"Proposed dates: {parsed_dates['dates_text']}"
                event.save()
                
                # Generate confirmation menu
                confirmation_msg = self.message_service.format_planner_confirmation_menu(event)
                return HandlerResult.success_response(confirmation_msg, 'awaiting_confirmation')
            else:
                return HandlerResult.error_response(
                    "I couldn't understand those dates. Please try again with a clearer format like '8/1-8/4' or 'Saturday and Sunday'."
                )
                
        except Exception as e:
            logger.error(f"Error in date collection: {e}")
            return HandlerResult.error_response("Sorry, there was an error processing the dates.")

class ConfirmationMenuHandler(BaseWorkflowHandler):
    """Handles the 3-option confirmation menu"""
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            choice = message.strip()
            
            if choice == '1':
                # Send availability requests
                for guest in event.guests:
                    self.guest_service.send_availability_request(guest)
                
                event.status = 'collecting_availability'
                event.save()
                
                return HandlerResult.success_response(
                    "💌 Availability requests sent via SMS!",
                    'collecting_availability'
                )
                
            elif choice == '2':
                # Change dates
                response_text = "What dates are you thinking for your event?\n\n"
                response_text += "You can say things like:\n"
                response_text += "- 'Saturday and Sunday'\n"
                response_text += "- '7/12,7/13,7/14'\n"
                response_text += "- '8/5-8/12'\n"
                response_text += "- 'friday to monday'"
                
                return HandlerResult.success_response(response_text, 'collecting_dates')
                
            elif choice == '3':
                # Add more guests
                return HandlerResult.transition_to('collecting_guests')
                
            else:
                return HandlerResult.error_response("Please reply with 1, 2, or 3 to choose an option.")
                
        except Exception as e:
            logger.error(f"Error in confirmation menu: {e}")
            return HandlerResult.error_response("Sorry, there was an error. Please try again.")

class VenueSelectionHandler(BaseWorkflowHandler):
    """Handles venue selection workflow stage"""
    
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        try:
            message_lower = message.lower().strip()
            
            if message.strip().isdigit():
                # Venue selection (1-3)
                return self._handle_venue_selection(event, int(message.strip()))
                
            elif 'new list' in message_lower:
                # Regenerate suggestions
                return self._generate_new_venue_list(event)
                
            elif 'activity' in message_lower:
                # Change activity
                response_text = "🎯 What would you like to do instead?\n\n"
                response_text += "Please describe the activity (e.g., 'boozy brunch', 'Chinese restaurant', 'coffee and catch up', etc.)"
                return HandlerResult.success_response(response_text, 'collecting_activity')
                
            elif 'location' in message_lower:
                # Change location
                response_text = "🌍 Where should the hangout be?\n\n"
                response_text += "Please specify a location (e.g., 'Williamsburg', 'Manhattan', 'St. Louis', etc.)"
                return HandlerResult.success_response(response_text, 'collecting_location')
                
            else:
                return HandlerResult.error_response(
                    "Please select a venue (1,2,3) or say:\n"
                    "- 'New list' for more options\n"
                    "- 'Activity' to change the activity\n"
                    "- 'Location' to change the location"
                )
                
        except Exception as e:
            logger.error(f"Error in venue selection: {e}")
            return HandlerResult.error_response("Sorry, there was an error. Please try again.")
    
    def _handle_venue_selection(self, event: Event, venue_number: int) -> HandlerResult:
        """Handle numeric venue selection"""
        try:
            if 1 <= venue_number <= 3:
                # Get stored venue suggestions
                import json
                venue_suggestions = json.loads(event.venue_suggestions or '[]')
                
                if venue_number <= len(venue_suggestions):
                    selected_venue = venue_suggestions[venue_number - 1]
                    
                    # Store selected venue
                    event.selected_venue = json.dumps(selected_venue)
                    event.save()
                    
                    # Generate final confirmation
                    confirmation_msg = self._generate_final_confirmation(event, selected_venue)
                    return HandlerResult.success_response(confirmation_msg, 'final_confirmation')
                else:
                    return HandlerResult.error_response("❌ Invalid selection. Please choose a number from the list.")
            else:
                return HandlerResult.error_response("❌ Invalid selection. Please choose a number from 1-3.")
                
        except Exception as e:
            logger.error(f"Error handling venue selection: {e}")
            return HandlerResult.error_response("Sorry, there was an error processing your selection.")
    
    def _generate_final_confirmation(self, event: Event, selected_venue: Dict) -> str:
        """Generate final event confirmation message"""
        date_obj = event.start_date
        formatted_date = date_obj.strftime('%A, %B %-d') if date_obj else "TBD"
        
        if event.start_time and event.end_time:
            start_time = event.start_time.strftime('%I:%M%p').lower()
            end_time = event.end_time.strftime('%I:%M%p').lower()
            time_str = f"{start_time}-{end_time}"
        else:
            time_str = "All day"
        
        guest_names = [guest.name for guest in event.guests if guest.name]
        attendees = ", ".join(guest_names) if guest_names else f"{len(event.guests)} guests"
        
        confirmation_msg = "🎉 Event Ready to Send!\n\n"
        confirmation_msg += f"📅 Date: {formatted_date}\n"
        confirmation_msg += f"🕒 Time: {time_str}\n"
        confirmation_msg += f"🏢 Activity: {selected_venue.get('name', 'Selected venue')}\n"
        confirmation_msg += f"👥 Attendees: {attendees}\n\n"
        confirmation_msg += "Would you like to:\n"
        confirmation_msg += "1. Send invitations to guests\n"
        confirmation_msg += "Or reply 'restart' to start over with a new event"
        
        return confirmation_msg
```

## SMS Route Implementation (Clean & Focused)

### Main SMS Route Handler
```python
from flask import Blueprint, request
from twilio.twiml.messaging_response import MessagingResponse
import logging

logger = logging.getLogger(__name__)

sms_bp = Blueprint("sms", __name__)

class SMSRouter:
    """Routes SMS messages to appropriate handlers"""
    
    def __init__(self):
        self.event_service = EventWorkflowService()
        self.guest_service = GuestManagementService()
        self.message_service = MessageFormattingService()
        self.ai_service = AIProcessingService()
        self.venue_service = VenueService()
        self.availability_service = AvailabilityService()
        
        # Initialize handlers
        self.handlers = {
            'collecting_guests': GuestCollectionHandler(
                self.event_service, self.guest_service, 
                self.message_service, self.ai_service
            ),
            'collecting_dates': DateCollectionHandler(
                self.event_service, self.guest_service,
                self.message_service, self.ai_service
            ),
            'awaiting_confirmation': ConfirmationMenuHandler(
                self.event_service, self.guest_service,
                self.message_service, self.ai_service
            ),
            'selecting_venue': VenueSelectionHandler(
                self.event_service, self.guest_service,
                self.message_service, self.ai_service
            )
            # Add other handlers as needed
        }
    
    def route_message(self, phone_number: str, message: str) -> str:
        """Main routing logic - everyone is a planner by default, guest mode per-message only"""
        try:
            # Normalize phone number
            normalized_phone = self._normalize_phone(phone_number)
            
            # Check if they're temporarily responding to an invitation/availability request
            guest_state = GuestState.query.filter_by(phone_number=normalized_phone).first()
            
            if guest_state:
                # Handle as guest (temporary override for responding to invitations)
                response = self._handle_guest_message(guest_state, message)
                
                # IMPORTANT: Always cleanup guest state after each message response
                # Don't wait for workflow completion - return to planner mode immediately
                self._cleanup_guest_state(guest_state)
                
                return response
            
            # Default: Handle as planner (everyone is a planner unless responding to invitations)
            planner = self._get_or_create_planner(normalized_phone)
            return self._handle_planner_message(planner, message)
            
        except Exception as e:
            logger.error(f"Error routing message: {e}")
            return self._create_error_response()
    
    def _handle_planner_message(self, planner: Planner, message: str) -> str:
        """Handle messages from planners"""
        try:
            # Check if name is needed
            if not planner.name:
                return self._handle_name_collection(planner, message)
            
            # Handle reset commands
            if message.lower().strip() in ['reset', 'restart', 'start over']:
                return self._handle_reset_command(planner)
            
            # Get active event
            active_event = self._get_active_event(planner.id)
            
            if active_event:
                return self._handle_workflow_message(active_event, message)
            else:
                return self._handle_new_event_request(planner, message)
                
        except Exception as e:
            logger.error(f"Error handling planner message: {e}")
            return self._create_error_response()
    
    def _handle_workflow_message(self, event: Event, message: str) -> str:
        """Route message to appropriate workflow handler"""
        try:
            handler = self.handlers.get(event.workflow_stage)
            
            if handler:
                result = handler.handle_message(event, message)
                
                if result.success:
                    # Update workflow stage if transition specified
                    if result.next_stage:
                        self.event_service.transition_to_stage(event, result.next_stage)
                    
                    return self._create_success_response(result.message)
                else:
                    return self._create_error_response(result.message)
            else:
                logger.warning(f"No handler for stage: {event.workflow_stage}")
                return self._create_error_response("I'm not sure how to help with that right now.")
                
        except Exception as e:
            logger.error(f"Error in workflow handling: {e}")
            return self._create_error_response()
    
    def _handle_guest_message(self, guest_state: GuestState, message: str) -> str:
        """Handle messages from guests with active states - single response per state"""
        try:
            current_state = guest_state.current_state
            
            if current_state == 'awaiting_availability':
                return self._handle_availability_response(guest_state, message)
            elif current_state == 'awaiting_rsvp':
                return self._handle_rsvp_response(guest_state, message)
            else:
                return self._cleanup_guest_state_and_redirect(guest_state)
                
        except Exception as e:
            logger.error(f"Error handling guest message: {e}")
            return self._create_error_response()
    
    def _handle_availability_response(self, guest_state: GuestState, message: str) -> str:
        """Handle guest availability response - single message, immediate cleanup"""
        try:
            # Parse availability using AI
            context = guest_state.get_state_data()
            parsed_availability = self.ai_service.parse_availability_text(message, context)
            
            if 'error' in parsed_availability:
                return self._create_error_response(
                    "I couldn't understand your availability. Please try again with a format like 'Monday 2-6pm' or 'Friday all day'."
                )
            
            # Save availability to database
            event = guest_state.event
            
            # Find corresponding guest record
            guest = Guest.query.filter_by(
                event_id=event.id,
                phone_number=guest_state.phone_number
            ).first()
            
            if not guest:
                return self._create_error_response("Sorry, I couldn't find your guest record.")
            
            # Save availability records
            for avail in parsed_availability.get('available_dates', []):
                availability = Availability(
                    event_id=event.id,
                    guest_id=guest.id,
                    date=datetime.strptime(avail['date'], '%Y-%m-%d').date(),
                    start_time=datetime.strptime(avail['start_time'], '%H:%M').time() if not avail['all_day'] else None,
                    end_time=datetime.strptime(avail['end_time'], '%H:%M').time() if not avail['all_day'] else None,
                    all_day=avail['all_day']
                )
                availability.save()
            
            # Update guest status
            guest.availability_provided = True
            guest.save()
            
            # Send confirmation and immediately return to planner mode
            response_text = "✅ Thanks! I've recorded your availability. "
            response_text += f"{event.planner.name} will use this to find the best time for everyone."
            
            return self._create_success_response(response_text)
            
        except Exception as e:
            logger.error(f"Error handling availability response: {e}")
            return self._create_error_response("Sorry, there was an error processing your availability.")
    
    def _handle_rsvp_response(self, guest_state: GuestState, message: str) -> str:
        """Handle guest RSVP response - single message, immediate cleanup"""
        try:
            message_lower = message.lower().strip()
            
            # Parse RSVP response
            if message_lower in ['yes', 'y', 'yep', 'yeah', 'sure', 'definitely']:
                rsvp_status = 'yes'
                response_text = "🎉 Great! You're confirmed for the event."
            elif message_lower in ['no', 'n', 'nope', 'can\'t make it', 'unable to attend']:
                rsvp_status = 'no'
                response_text = "Thanks for letting us know. We'll miss you!"
            elif message_lower in ['maybe', 'possibly', 'might', 'not sure', 'tentative']:
                rsvp_status = 'maybe'
                response_text = "Thanks! We've marked you as tentative."
            else:
                return self._create_error_response(
                    "Please reply 'Yes', 'No', or 'Maybe' to confirm your attendance!"
                )
            
            # Update guest RSVP status
            guest = Guest.query.filter_by(
                event_id=guest_state.event_id,
                phone_number=guest_state.phone_number
            ).first()
            
            if guest:
                guest.rsvp_status = rsvp_status
                guest.save()
            
            # Immediately return to planner mode (no confirmation needed)
            return self._create_success_response(response_text)
            
        except Exception as e:
            logger.error(f"Error handling RSVP response: {e}")
            return self._create_error_response("Sorry, there was an error processing your RSVP.")
    
    def _handle_name_collection(self, planner: Planner, message: str) -> str:
        """Handle initial name collection for new planners"""
        name = message.strip()
        
        # Check if it's a common greeting or command
        common_greetings = ['hey', 'hi', 'hello', 'sup', 'yo', 'howdy', 'hey there', 'hi there']
        commands = ['reset', 'restart', 'start over', 'help', 'status', 'events']
        
        if name.lower() in common_greetings or name.lower() in commands or len(name) < 2 or len(name) > 50:
            return self._create_success_response("What's your name? (This will be shown to your guests when they receive invitations)")
        
        # Save the name
        planner.name = name
        planner.save()
        
        # Create a basic event to start the workflow immediately
        event = Event(
            planner_id=planner.id,
            status='planning',
            workflow_stage='collecting_guests'
        )
        event.save()
        
        welcome_text = f"""Great to meet you, {name}! 👋
Let's plan your event!

Who's coming?

Reply with guest names and phone numbers (e.g. 'John Doe, 123-456-7890') or select previous contacts (e.g. '1,2').

Add one guest at a time.

💡 Commands:
- 'Remove contact'
- 'Restart'"""
        
        return self._create_success_response(welcome_text)
    
    def _get_or_create_planner(self, normalized_phone: str) -> Planner:
        """Get existing planner or create new one - everyone is a planner by default"""
        planner = Planner.query.filter_by(phone_number=normalized_phone).first()
        
        if not planner:
            # Create new planner - everyone starts as a planner
            planner = Planner(phone_number=normalized_phone)
            planner.save()
        
        return planner
    
    def _get_active_event(self, planner_id: int) -> Event:
        """Get active event for planner"""
        return Event.query.filter_by(
            planner_id=planner_id
        ).filter(
            Event.status.in_(['planning', 'collecting_availability', 'selecting_time'])
        ).filter(
            Event.workflow_stage.in_([
                'collecting_guests', 'removing_contacts', 'collecting_dates', 'awaiting_confirmation', 
                'collecting_availability', 'selecting_time', 'collecting_location', 
                'collecting_activity', 'selecting_venue', 'final_confirmation'
            ])
        ).filter(
            Event.status != 'finalized'
        ).order_by(Event.created_at.desc()).first()
    
    def _cleanup_guest_state(self, guest_state: GuestState) -> None:
        """Remove guest state to allow planner mode - called after every guest message"""
        try:
            guest_state.delete()
            logger.info(f"Cleaned up guest state for {guest_state.phone_number}")
        except Exception as e:
            logger.error(f"Error cleaning up guest state: {e}")
    
    def _cleanup_guest_state_and_redirect(self, guest_state: GuestState) -> str:
        """Clean up invalid guest state and redirect to planner mode"""
        phone_number = guest_state.phone_number
        self._cleanup_guest_state(guest_state)
        
        # Now handle as planner
        planner = self._get_or_create_planner(phone_number)
        return self._handle_planner_message(planner, "status")  # Default to status check
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to standard format"""
        # Remove + and non-digits
        digits = ''.join(filter(str.isdigit, phone))
        
        # Handle different formats
        if len(digits) == 11 and digits.startswith('1'):
            return digits[1:]  # Remove leading 1
        elif len(digits) == 10:
            return digits
        
        return digits
    
    def _create_success_response(self, message: str) -> str:
        """Create successful TwiML response"""
        resp = MessagingResponse()
        resp.message(message)
        return str(resp)
    
    def _create_error_response(self, message: str = None) -> str:
        """Create error TwiML response"""
        resp = MessagingResponse()
        error_msg = message or "Sorry, there was an error processing your message. Please try again."
        resp.message(error_msg)
        return str(resp)

@sms_bp.route("/incoming", methods=["POST"])
def handle_incoming_sms():
    """Twilio webhook endpoint for incoming SMS messages"""
    try:
        # Get message details
        from_number = request.form.get('From', '')
        message_body = request.form.get('Body', '').strip()
        
        logger.info(f"Incoming SMS from {from_number}: {message_body}")
        
        if not from_number or not message_body:
            logger.error("Missing required SMS parameters")
            return SMSRouter()._create_error_response()
        
        # Route message
        router = SMSRouter()
        return router.route_message(from_number, message_body)
        
    except Exception as e:
        logger.error(f"Error in SMS webhook: {e}")
        return SMSRouter()._create_error_response()
```

## Current Problems Solved

### 1. **Monolithic Functions → Handler Pattern**
- Replace 1000+ line functions with focused 50-100 line handlers
- Each handler manages one workflow stage from screenshots

### 2. **Hard-coded Workflows → State Machine**
- Explicit state transitions based on screenshot flows
- Centralized workflow management with validation

### 3. **Mixed Concerns → Service Layers**
- Separate message formatting from business logic
- Dedicated services for availability, venues, invitations

### 4. **Inconsistent Formatting → Template System**
- Standardized emoji and numbering patterns from screenshots
- Reusable message templates for common formats

### 5. **Complex Role Management → Everyone is a Planner by Default**
- **Simple Logic**: All users are planners unless temporarily responding to invitations
- GuestState created only when receiving availability/RSVP requests from other planners
- Automatic return to planner mode after completing guest responses
- Eliminates complex role detection and switching - much cleaner architecture

## Implementation Guidelines

### Error Handling Strategy
- Use structured exceptions with specific error codes
- Log all errors with context for debugging
- Provide user-friendly error messages with recovery guidance
- Implement graceful degradation when external services fail

### Database Best Practices
- Use transactions for multi-step operations
- Implement proper cascade deletes for related records
- Add database indexes for frequently queried fields
- Use connection pooling for production deployments

### SMS Integration Guidelines
- Validate phone numbers before processing
- Handle Twilio webhook retries properly
- Implement message length limits and pagination
- Add delivery status tracking for important messages

### AI Integration Best Practices
- Include confidence levels in AI responses
- Implement fallback strategies for AI failures
- Cache expensive AI operations when possible
- Validate AI outputs before using in business logic

### Security Considerations
- Validate and sanitize all user input
- Use environment variables for sensitive configuration
- Implement rate limiting for SMS endpoints
- Add authentication for admin endpoints

## Expected File Structure After Rebuild

```
app/
├── routes/
│   └── sms.py (150-200 lines, clean routing only)
├── services/
│   ├── event_service.py
│   ├── guest_service.py
│   ├── message_service.py
│   ├── venue_service.py
│   ├── availability_service.py
│   └── sms_service.py
├── handlers/
│   ├── base_handler.py
│   ├── guest_collection_handler.py
│   ├── date_collection_handler.py
│   ├── confirmation_menu_handler.py
│   ├── venue_selection_handler.py
│   └── [other workflow handlers]
├── models/
│   └── [existing models - may need updates]
└── utils/
    └── [keep existing utilities]
```

This comprehensive document provides everything needed to rebuild the SMS Event Planner with proper architecture, following the established patterns from screenshots while solving all the structural problems identified in the current implementation.
