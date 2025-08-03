from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import json

db = SQLAlchemy()


class BaseModel(db.Model):
    """Base model with common fields and methods."""
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), 
                          onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    def to_dict(self):
        """Convert model instance to dictionary."""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
    
    def save(self):
        """Save the model instance to the database."""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """Delete the model instance from the database."""
        db.session.delete(self)
        db.session.commit()


class Planner(BaseModel):
    """Planner model for event organizers."""
    __tablename__ = 'planners'
    
    phone_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    timezone = db.Column(db.String(50), default='UTC')
    preferences = db.Column(db.Text, nullable=True)  # JSON string for user preferences
    
    # Relationships
    events = db.relationship('Event', backref='planner', lazy=True, cascade='all, delete-orphan')
    contacts = db.relationship('Contact', backref='planner', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Planner {self.name or self.phone_number}>'
    
    def get_preferences(self):
        """Get user preferences as dictionary."""
        if self.preferences:
            try:
                return json.loads(self.preferences)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_preferences(self, prefs_dict):
        """Set user preferences from dictionary."""
        self.preferences = json.dumps(prefs_dict)


class Event(BaseModel):
    """Event model for planned events."""
    __tablename__ = 'events'
    
    planner_id = db.Column(db.Integer, db.ForeignKey('planners.id'), nullable=False)
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    activity = db.Column(db.String(200), nullable=True)
    location = db.Column(db.String(500), nullable=True)
    venue_info = db.Column(db.Text, nullable=True)  # JSON string for venue details
    venue_suggestions = db.Column(db.Text, nullable=True)  # JSON string for AI venue suggestions
    selected_venue = db.Column(db.Text, nullable=True)  # JSON string for selected venue
    
    # Event timing
    start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=True)
    start_time = db.Column(db.Time, nullable=True)  # Separate time field for scheduling
    end_time = db.Column(db.Time, nullable=True)    # Separate time field for scheduling
    duration_hours = db.Column(db.Float, nullable=True)
    
    # Event status and workflow
    status = db.Column(db.String(50), default='planning', nullable=False)
    workflow_stage = db.Column(db.String(100), default='initial', nullable=False)
    
    # Event metadata
    max_guests = db.Column(db.Integer, nullable=True)
    budget = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    guests = db.relationship('Guest', backref='event', lazy=True, cascade='all, delete-orphan')
    availability_requests = db.relationship('Availability', backref='event', lazy=True, cascade='all, delete-orphan')
    finalized_plans = db.relationship('FinalizedPlan', backref='event', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Event {self.title or "Untitled"}>'
    
    def get_venue_info(self):
        """Get venue information as dictionary."""
        if self.venue_info:
            try:
                return json.loads(self.venue_info)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_venue_info(self, venue_dict):
        """Set venue information from dictionary."""
        self.venue_info = json.dumps(venue_dict)


class Contact(BaseModel):
    """Contact model for planner's saved contacts."""
    __tablename__ = 'contacts'
    
    planner_id = db.Column(db.Integer, db.ForeignKey('planners.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Contact metadata
    tags = db.Column(db.String(500), nullable=True)  # Comma-separated tags
    last_contacted = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<Contact {self.name} ({self.phone_number})>'
    
    def get_tags_list(self):
        """Get tags as a list."""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    def set_tags_list(self, tags_list):
        """Set tags from a list."""
        self.tags = ', '.join(tags_list) if tags_list else None


class Guest(BaseModel):
    """Guest model for event participants."""
    __tablename__ = 'guests'
    
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    contact_id = db.Column(db.Integer, db.ForeignKey('contacts.id'), nullable=True)
    
    # Guest information
    name = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    location = db.Column(db.String(200), nullable=True)
    
    # RSVP and participation
    invitation_sent_at = db.Column(db.DateTime, nullable=True)
    rsvp_status = db.Column(db.String(20), default='pending')  # pending, accepted, declined, maybe
    availability_provided = db.Column(db.Boolean, default=False)
    
    # Guest metadata
    dietary_restrictions = db.Column(db.String(500), nullable=True)
    special_requirements = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    availability_entries = db.relationship('Availability', backref='guest', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Guest {self.name or self.phone_number} for {self.event.title}>'


class Availability(BaseModel):
    """Availability model for guest scheduling."""
    __tablename__ = 'availability'
    
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    guest_id = db.Column(db.Integer, db.ForeignKey('guests.id'), nullable=True)
    
    # Availability timing
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    all_day = db.Column(db.Boolean, default=False)
    
    # Availability metadata
    preference_level = db.Column(db.String(20), default='available')  # available, preferred, unavailable
    notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        guest_name = self.guest.name if self.guest else 'Unknown'
        return f'<Availability {guest_name} on {self.date}>'


class FinalizedPlan(BaseModel):
    """Finalized plan model for confirmed events."""
    __tablename__ = 'finalized_plans'
    
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    
    # Finalized details
    final_date = db.Column(db.DateTime, nullable=False)
    final_location = db.Column(db.String(500), nullable=False)
    final_venue_info = db.Column(db.Text, nullable=True)  # JSON string
    
    # Plan metadata
    confirmed_guest_count = db.Column(db.Integer, nullable=True)
    total_cost = db.Column(db.Float, nullable=True)
    calendar_event_id = db.Column(db.String(200), nullable=True)
    
    # Communication
    announcement_sent_at = db.Column(db.DateTime, nullable=True)
    reminder_sent_at = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<FinalizedPlan for {self.event.title} on {self.final_date}>'
    
    def get_final_venue_info(self):
        """Get final venue information as dictionary."""
        if self.final_venue_info:
            try:
                return json.loads(self.final_venue_info)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_final_venue_info(self, venue_dict):
        """Set final venue information from dictionary."""
        self.final_venue_info = json.dumps(venue_dict)


class GuestState(BaseModel):
    """Guest conversation state model for SMS workflow management."""
    __tablename__ = 'guest_states'
    
    phone_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    current_state = db.Column(db.String(100), nullable=False)
    state_data = db.Column(db.Text, nullable=True)  # JSON string for state-specific data
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=True)
    
    # State metadata
    last_activity = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    retry_count = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<GuestState {self.phone_number}: {self.current_state}>'
    
    def get_state_data(self):
        """Get state data as dictionary."""
        if self.state_data:
            try:
                return json.loads(self.state_data)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_state_data(self, data_dict):
        """Set state data from dictionary."""
        self.state_data = json.dumps(data_dict) if data_dict else None
        self.last_activity = datetime.now(timezone.utc)
