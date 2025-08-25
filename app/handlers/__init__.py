from abc import ABC, abstractmethod
from typing import Dict, Optional
from dataclasses import dataclass
from app.models.event import Event
from app.services import (
    EventWorkflowService, 
    GuestManagementService,
    MessageFormattingService,
    AIProcessingService
)

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
                 ai_service: AIProcessingService,
                 venue_service=None):
        self.event_service = event_service
        self.guest_service = guest_service
        self.message_service = message_service
        self.ai_service = ai_service
        self.venue_service = venue_service
    
    @abstractmethod
    def handle_message(self, event: Event, message: str) -> HandlerResult:
        """Process message for this workflow stage"""
        pass
    
    def validate_input(self, message: str, context: Dict) -> bool:
        """Validate input for this stage"""
        return len(message.strip()) > 0
