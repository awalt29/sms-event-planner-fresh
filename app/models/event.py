from sqlalchemy import Column, Integer, String, Date, Time, Text, JSON, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.models import BaseModel

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
    
    # Selected time from availability overlaps
    selected_date = Column(Date, nullable=True)
    selected_start_time = Column(Time, nullable=True)
    selected_end_time = Column(Time, nullable=True)
    
    # Workflow management
    workflow_stage = Column(String(50), nullable=False, default='collecting_guests')
    previous_workflow_stage = Column(String(50), nullable=True)  # For add guest workflow
    status = Column(String(20), nullable=False, default='planning')
    
    # Venue management
    venue_suggestions = Column(JSON, nullable=True)
    selected_venue = Column(JSON, nullable=True)
    
    # Availability calculation results
    available_windows = Column(JSON, nullable=True)  # Stores calculated overlaps
    
    # Notes and workflow data
    notes = Column(Text, nullable=True)
    
    # Relationships
    planner = relationship("Planner", back_populates="events")
    guests = relationship("Guest", back_populates="event", cascade="all, delete-orphan")
    guest_states = relationship("GuestState", back_populates="event", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Event {self.title or self.id} - {self.workflow_stage}>'
