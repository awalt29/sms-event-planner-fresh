from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from app.models.event import Event
from app.models.planner import Planner
from app.models.contact import Contact
from app.models.guest import Guest
from app.models.guest_state import GuestState
from app import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
def index():
    """Dashboard homepage with overview stats"""
    try:
        total_events = Event.query.count()
        total_planners = Planner.query.count()
        total_contacts = Contact.query.count()
        
        recent_events = Event.query.order_by(Event.created_at.desc()).limit(5).all()
        recent_events_count = len([e for e in Event.query.all() 
                                 if (datetime.now() - e.created_at).days <= 7])
        
        # Events by stage
        events = Event.query.all()
        events_by_stage = {}
        for event in events:
            stage = event.workflow_stage
            events_by_stage[stage] = events_by_stage.get(stage, 0) + 1
        
        return render_template('index.html',
                                 event_count=total_events,
                                 planner_count=total_planners,
                                 contact_count=total_contacts,
                                 recent_event_count=recent_events_count,
                                 recent_events=recent_events,
                                 events_by_stage=events_by_stage)
    except Exception as e:
        logger.error(f"Dashboard index error: {e}")
        flash('Error loading dashboard', 'error')
        return render_template('index.html', 
                             event_count=0,
                             planner_count=0,
                             contact_count=0,
                             recent_event_count=0,
                             recent_events=[],
                             events_by_stage={})

@dashboard_bp.route('/events')
def events():
    """Events overview page"""
    try:
        events = Event.query.order_by(Event.created_at.desc()).all()
        
        # Calculate events by stage
        stage_counts = {}
        for event in events:
            stage = event.workflow_stage
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
        
        return render_template('events.html', events=events, events_by_stage=stage_counts)
    except Exception as e:
        logger.error(f"Events page error: {e}")
        flash('Error loading events', 'error')
        return render_template('events.html', events=[], events_by_stage={})

@dashboard_bp.route('/planners')
def planners():
    """Planner management page"""
    try:
        planners = Planner.query.order_by(Planner.created_at.desc()).all()
        
        # Sort planners by event count for the activity section
        planners_by_activity = sorted(planners, key=lambda p: len(p.events), reverse=True)[:5]
        
        # Calculate statistics
        total_events_by_planners = sum(len(p.events) for p in planners)
        total_contacts_by_planners = sum(len(p.contacts) for p in planners)
        active_planners_count = len([p for p in planners if len(p.events) > 0])
        avg_events_per_planner = total_events_by_planners / len(planners) if planners else 0
        
        return render_template('planners.html', 
                             planners=planners, 
                             planners_by_activity=planners_by_activity,
                             total_events_by_planners=total_events_by_planners,
                             total_contacts_by_planners=total_contacts_by_planners,
                             active_planners_count=active_planners_count,
                             avg_events_per_planner=avg_events_per_planner)
    except Exception as e:
        logger.error(f"Planners page error: {e}")
        flash('Error loading planners', 'error')
        return render_template('planners.html', 
                             planners=[], 
                             planners_by_activity=[],
                             total_events_by_planners=0,
                             total_contacts_by_planners=0,
                             active_planners_count=0,
                             avg_events_per_planner=0)

@dashboard_bp.route('/contacts')
def contacts():
    """Contact management page"""
    try:
        contacts = Contact.query.order_by(Contact.created_at.desc()).all()
        
        # Sort contacts by guest count (number of events they've been invited to)
        contacts_by_activity = sorted(contacts, key=lambda c: len(c.guests), reverse=True)[:5]
        
        # Calculate statistics
        contacts_with_events = len([c for c in contacts if len(c.guests) > 0])
        total_invitations = sum(len(c.guests) for c in contacts)
        avg_events_per_contact = total_invitations / len(contacts) if contacts else 0
        unique_planners_count = len(set(c.planner_id for c in contacts))
        
        return render_template('contacts.html', 
                             contacts=contacts,
                             contacts_by_activity=contacts_by_activity,
                             contacts_with_events=contacts_with_events,
                             total_invitations=total_invitations,
                             avg_events_per_contact=avg_events_per_contact,
                             unique_planners_count=unique_planners_count)
    except Exception as e:
        logger.error(f"Contacts page error: {e}")
        flash('Error loading contacts', 'error')
        return render_template('contacts.html', 
                             contacts=[], 
                             contacts_by_activity=[],
                             contacts_with_events=0,
                             total_invitations=0,
                             avg_events_per_contact=0,
                             unique_planners_count=0)

@dashboard_bp.route('/planner/<int:planner_id>/delete', methods=['POST'])
def delete_planner(planner_id):
    """Delete a specific planner and all their data"""
    try:
        planner = Planner.query.get_or_404(planner_id)
        planner_name = planner.name
        planner_phone = planner.phone_number
        
        # Delete all guests for this planner's events
        for event in planner.events:
            Guest.query.filter_by(event_id=event.id).delete()
        
        # Delete all guest states for this planner
        GuestState.query.filter_by(phone_number=planner.phone_number).delete()
        
        # Delete all events created by this planner
        Event.query.filter_by(planner_id=planner_id).delete()
        
        # Delete all contacts belonging to this planner
        Contact.query.filter_by(planner_id=planner_id).delete()
        
        # Delete the planner
        db.session.delete(planner)
        db.session.commit()
        
        flash(f'Planner {planner_name} ({planner_phone}) deleted successfully', 'success')
        
    except Exception as e:
        logger.error(f"Error deleting planner {planner_id}: {e}")
        db.session.rollback()
        flash('Error deleting planner', 'error')
    
    return redirect(url_for('dashboard.planners'))

@dashboard_bp.route('/contact/<int:contact_id>/delete', methods=['POST'])
def delete_contact(contact_id):
    """Delete a specific contact"""
    try:
        contact = Contact.query.get_or_404(contact_id)
        contact_name = contact.name
        contact_phone = contact.phone_number
        
        db.session.delete(contact)
        db.session.commit()
        
        flash(f'Contact {contact_name} ({contact_phone}) deleted successfully', 'success')
        
    except Exception as e:
        logger.error(f"Error deleting contact {contact_id}: {e}")
        db.session.rollback()
        flash('Error deleting contact', 'error')
    
    return redirect(url_for('dashboard.contacts'))

@dashboard_bp.route('/reset-database', methods=['POST'])
def reset_database():
    """Clear the entire database - DANGER ZONE"""
    try:
        # Delete all data in correct order (respect foreign keys)
        Guest.query.delete()
        GuestState.query.delete()
        Contact.query.delete()
        Event.query.delete()
        Planner.query.delete()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': '🗑️ Database completely reset! All data has been cleared.'})
        
    except Exception as e:
        logger.error(f"Error resetting database: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Error resetting database'}), 500
