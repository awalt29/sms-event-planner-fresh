from typing import Dict, List, Optional
from datetime import datetime, date
import logging
from app.models.event import Event
from app.models.planner import Planner

logger = logging.getLogger(__name__)

class EventWorkflowService:
    """Manages event planning workflow and state transitions"""
    
    def __init__(self):
        from app.services.message_formatting_service import MessageFormattingService
        from app.services.ai_processing_service import AIProcessingService
        self.message_formatter = MessageFormattingService()
        self.ai_service = AIProcessingService()
    
    def create_event_from_text(self, planner_id: int, text: str) -> Dict:
        """Create new event from natural language description"""
        try:
            # Parse event details using AI
            parsed_event = self.ai_service.parse_event_input(text)
            
            # Create event record
            event = Event(
                planner_id=planner_id,
                title=parsed_event.get('title'),
                location=parsed_event.get('location'),
                activity=parsed_event.get('activity'),
                workflow_stage='collecting_guests',
                status='planning'
            )
            event.save()
            
            return {'success': True, 'event': event}
            
        except Exception as e:
            logger.error(f"Error creating event: {e}")
            return {'success': False, 'error': str(e)}
    
    def transition_to_stage(self, event: Event, new_stage: str) -> bool:
        """Validate and execute workflow state transition"""
        valid_transitions = self._get_valid_transitions(event.workflow_stage)
        
        if new_stage in valid_transitions:
            event.workflow_stage = new_stage
            event.save()
            return True
        
        logger.warning(f"Invalid transition from {event.workflow_stage} to {new_stage}")
        return False
    
    def _get_valid_transitions(self, current_stage: str) -> List[str]:
        """Get valid next stages for current workflow stage"""
        transitions = {
            'collecting_guests': ['collecting_dates', 'removing_contacts'],
            'collecting_dates': ['awaiting_confirmation'],
            'awaiting_confirmation': ['collecting_availability', 'collecting_dates', 'collecting_guests'],
            'collecting_availability': ['selecting_time', 'collecting_guests'],
            'selecting_time': ['collecting_location'],
            'collecting_location': ['collecting_activity'],
            'collecting_activity': ['selecting_venue'],
            'selecting_venue': ['final_confirmation', 'collecting_activity', 'collecting_location'],
            'final_confirmation': ['finalized']
        }
        return transitions.get(current_stage, [])
