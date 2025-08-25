from sqlalchemy import Column, Integer, String, DateTime, Date, Time, Boolean, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import json
from app import db

class BaseModel(db.Model):
    """Base model with common fields and methods"""
    __abstract__ = True
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def save(self):
        """Save instance to database"""
        db.session.add(self)
        db.session.commit()
    
    def delete(self):
        """Delete instance from database"""
        db.session.delete(self)
        db.session.commit()
    
    def to_dict(self):
        """Convert instance to dictionary"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
