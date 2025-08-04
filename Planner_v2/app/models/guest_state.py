from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.models import BaseModel
import json

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
    
    def __repr__(self):
        return f'<GuestState {self.phone_number} - {self.current_state}>'
