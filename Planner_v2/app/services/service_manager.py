"""
Singleton Service Manager for Performance Optimization

This module provides shared service instances to avoid recreating
services for every SMS message. Services are created once and reused.
"""

from app.services import (
    EventWorkflowService,
    GuestManagementService,
    MessageFormattingService,
    AIProcessingService,
    VenueService,
    AvailabilityService
)

class ServiceManager:
    """Singleton manager for shared service instances"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        # Only initialize once, even if called multiple times
        if not self._initialized:
            self._initialize_services()
            ServiceManager._initialized = True
    
    def _initialize_services(self):
        """Initialize all services once"""
        self.event_service = EventWorkflowService()
        self.guest_service = GuestManagementService()
        self.message_service = MessageFormattingService()
        self.ai_service = AIProcessingService()
        self.venue_service = VenueService()
        self.availability_service = AvailabilityService()
    
    def get_services(self):
        """Get all service instances as a tuple for easy unpacking"""
        return (
            self.event_service,
            self.guest_service, 
            self.message_service,
            self.ai_service,
            self.venue_service,
            self.availability_service
        )

# Module-level function for easy access
def get_shared_services():
    """Get shared service instances - creates singleton if needed"""
    manager = ServiceManager()
    return manager.get_services()
