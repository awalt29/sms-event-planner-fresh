from sqlalchemy import Column, Integer, String, Date, Time, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.models import BaseModel

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
    
    def __repr__(self):
        return f'<Availability {self.guest.name if self.guest else "Unknown"} - {self.date}>'
