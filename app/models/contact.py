from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.models import BaseModel

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
    
    def __repr__(self):
        return f'<Contact {self.name} - {self.phone_number}>'
