from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.models import BaseModel

class Planner(BaseModel):
    """Event planners who organize hangouts"""
    __tablename__ = 'planners'
    
    phone_number = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)
    
    # Relationships
    events = relationship("Event", back_populates="planner", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="planner", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Planner {self.name or self.phone_number}>'
