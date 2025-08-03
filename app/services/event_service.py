from typing import Dict, Any, List
from app.models import db, Event, Planner
from app.utils.ai import parse_event_input
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EventService:
    """Service class for event-related business logic."""
    
    def create_event_from_text(self, planner_id: int, text: str) -> Dict[str, Any]:
        """
        Create a new event from natural language text.
        
        Args:
            planner_id: ID of the planner creating the event
            text: Natural language description of the event
            
        Returns:
            dict: Result with success status and event or error details
        """
        try:
            # Parse the event details using AI
            parsed_event = parse_event_input(text)
            
            if parsed_event.get('error'):
                return {
                    'success': False,
                    'error': 'Could not understand the event description. Please try again with more details.'
                }
            
            # Create event with parsed information
            event = Event(
                planner_id=planner_id,
                title='Hangout',  # Simple default title for all events
                description=parsed_event.get('description'),
                activity=parsed_event.get('activity'),
                location=parsed_event.get('location'),
                duration_hours=parsed_event.get('duration'),
                max_guests=parsed_event.get('guest_count'),
                budget=parsed_event.get('budget'),
                status='planning',
                workflow_stage='collecting_guests'  # Start with guest collection
            )
            
            # Parse date if provided
            if parsed_event.get('date'):
                try:
                    event.start_date = datetime.strptime(parsed_event['date'], '%Y-%m-%d')
                except ValueError:
                    logger.warning(f"Could not parse date: {parsed_event['date']}")
            
            # Save special requirements as notes
            if parsed_event.get('special_requirements'):
                requirements_text = ', '.join(parsed_event['special_requirements'])
                event.notes = f"Special requirements: {requirements_text}"
            
            event.save()
            
            logger.info(f"Created event '{event.title}' for planner {planner_id}")
            
            return {
                'success': True,
                'event': event,
                'confidence': parsed_event.get('confidence', 'medium')
            }
            
        except Exception as e:
            logger.error(f"Error creating event from text: {e}")
            return {
                'success': False,
                'error': 'Failed to create event. Please try again.'
            }
    
    def update_event_status(self, event_id: int, new_status: str) -> Dict[str, Any]:
        """
        Update event status and workflow stage.
        
        Args:
            event_id: ID of the event to update
            new_status: New status for the event
            
        Returns:
            dict: Result with success status
        """
        try:
            event = Event.query.get(event_id)
            if not event:
                return {
                    'success': False,
                    'error': 'Event not found'
                }
            
            old_status = event.status
            event.status = new_status
            
            # Update workflow stage based on status
            status_to_stage = {
                'planning': 'initial',
                'collecting_availability': 'availability_collection',
                'scheduling': 'finding_time',
                'confirmed': 'finalized',
                'cancelled': 'cancelled'
            }
            
            event.workflow_stage = status_to_stage.get(new_status, event.workflow_stage)
            event.save()
            
            logger.info(f"Updated event {event_id} status from {old_status} to {new_status}")
            
            return {
                'success': True,
                'event': event,
                'old_status': old_status,
                'new_status': new_status
            }
            
        except Exception as e:
            logger.error(f"Error updating event status: {e}")
            return {
                'success': False,
                'error': 'Failed to update event status'
            }
    
    def get_events_for_planner(self, planner_id: int, status: str = None) -> List[Event]:
        """
        Get events for a specific planner.
        
        Args:
            planner_id: ID of the planner
            status: Optional status filter
            
        Returns:
            list: List of events
        """
        try:
            query = Event.query.filter_by(planner_id=planner_id)
            
            if status:
                query = query.filter_by(status=status)
            
            events = query.order_by(Event.created_at.desc()).all()
            
            logger.info(f"Retrieved {len(events)} events for planner {planner_id}")
            return events
            
        except Exception as e:
            logger.error(f"Error getting events for planner: {e}")
            return []
    
    def get_event_summary(self, event_id: int) -> Dict[str, Any]:
        """
        Get a comprehensive summary of an event.
        
        Args:
            event_id: ID of the event
            
        Returns:
            dict: Event summary with guest and availability information
        """
        try:
            event = Event.query.get(event_id)
            if not event:
                return {
                    'success': False,
                    'error': 'Event not found'
                }
            
            # Count guests by RSVP status
            rsvp_counts = {
                'accepted': 0,
                'declined': 0,
                'maybe': 0,
                'pending': 0
            }
            
            availability_count = 0
            
            for guest in event.guests:
                rsvp_counts[guest.rsvp_status] += 1
                if guest.availability_provided:
                    availability_count += 1
            
            summary = {
                'success': True,
                'event': event,
                'guest_count': len(event.guests),
                'rsvp_summary': rsvp_counts,
                'availability_responses': availability_count,
                'pending_availability': len(event.guests) - availability_count,
                'has_venue': bool(event.location),
                'has_date': bool(event.start_date),
                'workflow_completion': self._calculate_workflow_completion(event)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting event summary: {e}")
            return {
                'success': False,
                'error': 'Failed to get event summary'
            }
    
    def _calculate_workflow_completion(self, event: Event) -> Dict[str, Any]:
        """
        Calculate completion percentage of event planning workflow.
        
        Args:
            event: Event object
            
        Returns:
            dict: Workflow completion information
        """
        steps = {
            'event_created': True,  # Always true if we have an event
            'guests_added': len(event.guests) > 0,
            'availability_collected': all(guest.availability_provided for guest in event.guests) if event.guests else False,
            'time_scheduled': bool(event.start_date),
            'venue_confirmed': bool(event.location),
            'event_finalized': event.status == 'confirmed'
        }
        
        completed_steps = sum(1 for completed in steps.values() if completed)
        total_steps = len(steps)
        completion_percentage = (completed_steps / total_steps) * 100
        
        return {
            'steps': steps,
            'completed_steps': completed_steps,
            'total_steps': total_steps,
            'completion_percentage': completion_percentage,
            'next_step': self._get_next_step(steps)
        }
    
    def _get_next_step(self, steps: Dict[str, bool]) -> str:
        """
        Determine the next step in the event planning workflow.
        
        Args:
            steps: Dictionary of workflow steps and their completion status
            
        Returns:
            str: Description of the next step
        """
        if not steps['guests_added']:
            return "Add guests to your event"
        elif not steps['availability_collected']:
            return "Collect availability from all guests"
        elif not steps['time_scheduled']:
            return "Schedule the event time"
        elif not steps['venue_confirmed']:
            return "Confirm the venue"
        elif not steps['event_finalized']:
            return "Finalize and send out confirmations"
        else:
            return "Event planning complete!"
