#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/aaronwalters/Planner_app_live/Planner_v2')

from typing import Dict
from app.models.event import Event
from app.models.guest import Guest  
from app.models.availability import Availability
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_data_integrity_check():
    """Run data integrity check without circular imports"""
    
    # Create app context manually
    import os
    from flask import Flask
    from flask_sqlalchemy import SQLAlchemy
    
    app = Flask(__name__)
    
    # Configure database
    basedir = os.path.abspath(os.path.dirname(__file__))
    database_path = os.path.join(basedir, '../../instance/event_planner.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    from app.models import db
    db.init_app(app)
    
    with app.app_context():
        print("🔍 Data Integrity Check")
        print("=" * 30)
        
        # Check for corruption issues
        results = {
            'total_events': Event.query.count(),
            'total_guests': Guest.query.count(),
            'total_availability': Availability.query.count(),
            'orphaned_availability': 0,
            'wrong_event_availability': 0,
            'duplicate_availability': 0
        }
        
        print(f"Events: {results['total_events']}")
        print(f"Guests: {results['total_guests']}")
        print(f"Availability records: {results['total_availability']}")
        
        # Check for orphaned availability
        orphaned = Availability.query.filter(
            ~Availability.guest_id.in_(
                Guest.query.with_entities(Guest.id).subquery()
            )
        ).all()
        results['orphaned_availability'] = len(orphaned)
        
        # Check for wrong-event availability
        wrong_event_count = 0
        for avail in Availability.query.all():
            if avail.guest and avail.guest.event_id != avail.event_id:
                wrong_event_count += 1
        results['wrong_event_availability'] = wrong_event_count
        
        # Check for duplicates
        duplicate_count = 0
        for guest in Guest.query.all():
            guest_availability = Availability.query.filter_by(guest_id=guest.id).all()
            date_groups = {}
            for avail in guest_availability:
                key = (avail.event_id, avail.date.isoformat() if avail.date else None)
                date_groups[key] = date_groups.get(key, 0) + 1
            
            for key, count in date_groups.items():
                if count > 1:
                    duplicate_count += count - 1
        results['duplicate_availability'] = duplicate_count
        
        print(f"\n🔍 Issues Found:")
        print(f"Orphaned availability: {results['orphaned_availability']}")
        print(f"Wrong-event availability: {results['wrong_event_availability']}")
        print(f"Duplicate availability: {results['duplicate_availability']}")
        
        total_issues = results['orphaned_availability'] + results['wrong_event_availability'] + results['duplicate_availability']
        
        if total_issues == 0:
            print(f"\n✅ Database is clean! No integrity issues found.")
        else:
            print(f"\n⚠️  Found {total_issues} total integrity issues.")
        
        return results

if __name__ == "__main__":
    run_data_integrity_check()
