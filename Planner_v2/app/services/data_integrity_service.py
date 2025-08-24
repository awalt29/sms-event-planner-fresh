#!/usr/bin/env python3

import os
import sys
sys.path.append('/Users/aaronwalters/Planner_app_live/Planner_v2')

from typing import Dict
from flask import current_app
from app.models.event import Event
from app.models.guest import Guest
from app.models.availability import Availability
import logging

logger = logging.getLogger(__name__)

class DataIntegrityService:
    """Service to ensure database integrity and prevent corruption"""
    
    def __init__(self):
        # No app creation here - use current_app when needed
        pass
    
    def check_and_fix_all_issues(self) -> Dict[str, int]:
        """Comprehensive check and fix for all data integrity issues"""
        # This method should only be called within an app context
        results = {
            'orphaned_availability': 0,
            'wrong_event_availability': 0,
            'duplicate_availability': 0,
            'orphaned_guests': 0
        }
        
        # 1. Fix orphaned availability records (availability without valid guests)
        results['orphaned_availability'] = self._fix_orphaned_availability()
        
        # 2. Fix wrong-event availability records
        results['wrong_event_availability'] = self._fix_wrong_event_availability()
        
        # 3. Fix duplicate availability records
        results['duplicate_availability'] = self._fix_duplicate_availability()
        
        # 4. Fix orphaned guests (guests without events)
        results['orphaned_guests'] = self._fix_orphaned_guests()
        
        return results
    
    def _fix_orphaned_availability(self) -> int:
        """Remove availability records that don't have valid guests"""
        orphaned = Availability.query.filter(
            ~Availability.guest_id.in_(
                Guest.query.with_entities(Guest.id).subquery()
            )
        ).all()
        
        count = len(orphaned)
        for record in orphaned:
            logger.info(f"Removing orphaned availability record {record.id}")
            record.delete()
        
        return count
    
    def _fix_wrong_event_availability(self) -> int:
        """Fix availability records pointing to wrong events"""
        wrong_event_records = []
        for avail in Availability.query.all():
            if avail.guest and avail.guest.event_id != avail.event_id:
                wrong_event_records.append(avail)
        
        count = len(wrong_event_records)
        for record in wrong_event_records:
            logger.info(f"Fixing wrong-event availability: guest {record.guest.name}, correcting event_id from {record.event_id} to {record.guest.event_id}")
            record.event_id = record.guest.event_id
            record.save()
        
        return count
    
    def _fix_duplicate_availability(self) -> int:
        """Remove duplicate availability records, keeping the best one"""
        duplicates_removed = 0
        
        for guest in Guest.query.all():
            guest_availability = Availability.query.filter_by(guest_id=guest.id).all()
            
            # Group by (event_id, date)
            date_groups = {}
            for avail in guest_availability:
                key = (avail.event_id, avail.date.isoformat() if avail.date else None)
                if key not in date_groups:
                    date_groups[key] = []
                date_groups[key].append(avail)
            
            # Remove duplicates within each group
            for key, records in date_groups.items():
                if len(records) > 1:
                    # Score records to keep the best one
                    def score_record(r):
                        score = 0
                        # Penalize 23:59 end times (likely corrupted)
                        if r.end_time and r.end_time.hour == 23 and r.end_time.minute == 59:
                            score -= 100
                        # Prefer reasonable times
                        if r.end_time and 17 <= r.end_time.hour <= 23:
                            score += 10
                        # Prefer newer records (higher ID)
                        score += r.id * 0.001
                        return score
                    
                    records.sort(key=score_record, reverse=True)
                    keep_record = records[0]
                    
                    # Remove duplicates
                    for record in records[1:]:
                        logger.info(f"Removing duplicate availability: guest {guest.name}, date {record.date}, time {record.start_time}-{record.end_time}")
                        record.delete()
                        duplicates_removed += 1
        
        return duplicates_removed
    
    def _fix_orphaned_guests(self) -> int:
        """Remove guests that don't belong to valid events"""
        orphaned = Guest.query.filter(
            ~Guest.event_id.in_(
                Event.query.with_entities(Event.id).subquery()
            )
        ).all()
        
        count = len(orphaned)
        for guest in orphaned:
            logger.info(f"Removing orphaned guest {guest.name} (event_id: {guest.event_id})")
            # Also remove their availability records
            for avail in guest.availability_records:
                avail.delete()
            guest.delete()
        
        return count
    
    def run_preventive_maintenance(self) -> None:
        """Run regular maintenance to prevent corruption"""
        with self.app.app_context():
            logger.info("Running preventive data maintenance...")
            results = self.check_and_fix_all_issues()
            
            total_fixed = sum(results.values())
            if total_fixed > 0:
                logger.warning(f"Fixed {total_fixed} data integrity issues: {results}")
            else:
                logger.info("Data integrity check passed - no issues found")

if __name__ == "__main__":
    service = DataIntegrityService()
    service.run_preventive_maintenance()
