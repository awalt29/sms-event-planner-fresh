from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.models import BaseModel

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
    preferences_provided = Column(Boolean, nullable=False, default=False)
    preferences = Column(Text, nullable=True)
    
    # Relationships
    event = relationship("Event", back_populates="guests")
    contact = relationship("Contact", back_populates="guests")
    availability_records = relationship("Availability", back_populates="guest", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Guest {self.name} - {self.rsvp_status}>'
