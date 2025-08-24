import sys
sys.path.append('.')

from app import create_app, db
from app.models.event import Event
from app.models.planner import Planner
from app.models.guest import Guest
from app.models.availability import Availability
from app.services.message_formatting_service import MessageFormattingService
from datetime import datetime, date, time as dt_time

print('🧪 Testing Enhanced No Overlap Message')
print('=' * 50)

app = create_app()

with app.app_context():
    # Clean up and recreate test data
    planner = Planner.query.filter_by(phone_number='1234567890').first()
    if planner:
        db.session.delete(planner)
        db.session.commit()
    
    planner = Planner(phone_number='1234567890', name='Test Planner')
    db.session.add(planner)
    db.session.commit()
    
    event = Event(planner_id=planner.id, title='Test Party', workflow_stage='collecting_availability')
    db.session.add(event)
    db.session.commit()
    
    # Add event dates - using current year dates (Dec 19 is Friday, Dec 20 is Saturday in 2025)
    friday = date(2025, 12, 19)
    saturday = date(2025, 12, 20)
    
    # Create guests with non-overlapping availability
    john = Guest(event_id=event.id, name='John Doe', phone_number='1111111111', availability_provided=True)
    jane = Guest(event_id=event.id, name='Jane Smith', phone_number='2222222222', availability_provided=True)
    db.session.add_all([john, jane])
    db.session.commit()
    
    # Add non-overlapping availability
    # Friday: Jane available, John not
    jane_friday = Availability(
        event_id=event.id,
        guest_id=jane.id,
        date=friday,
        start_time=dt_time(19, 0),  # 7 PM
        end_time=dt_time(23, 0),    # 11 PM
        preference_level='available'
    )
    
    # Saturday: John available, Jane available but different times
    john_saturday = Availability(
        event_id=event.id,
        guest_id=john.id,
        date=saturday,
        start_time=dt_time(14, 0),  # 2 PM
        end_time=dt_time(18, 0),    # 6 PM
        preference_level='available'
    )
    
    jane_saturday = Availability(
        event_id=event.id,
        guest_id=jane.id,
        date=saturday,
        start_time=dt_time(18, 0),  # 6 PM
        end_time=dt_time(22, 0),    # 10 PM
        preference_level='available'
    )
    
    db.session.add_all([jane_friday, john_saturday, jane_saturday])
    db.session.commit()
    
    # Test the enhanced no overlap message
    formatting_service = MessageFormattingService()
    no_overlap_message = formatting_service.format_time_selection_options([], event)
    
    print('Enhanced no overlap message:')
    print('=' * 60)
    print(no_overlap_message)
    print('=' * 60)
    
    # Check for key elements
    checks = [
        ('❌ No overlapping times found.' in no_overlap_message, 'Main error message'),
        ('Guest availability:' in no_overlap_message, 'Guest availability header'),
        ('📅 Friday, December 19' in no_overlap_message, 'Friday date header'),
        ('📅 Saturday, December 20' in no_overlap_message, 'Saturday date header'),
        ('👤 John Doe' in no_overlap_message, 'John Doe name'),
        ('👤 Jane Smith' in no_overlap_message, 'Jane Smith name'),
        ('- Not available' in no_overlap_message, 'Not available text'),
        ('🕒 7pm - 11pm' in no_overlap_message, 'Jane Friday time'),
        ('🕒 2pm - 6pm' in no_overlap_message, 'John Saturday time'),
        ('🕒 6pm - 10pm' in no_overlap_message, 'Jane Saturday time'),
        ("Say 'restart'" in no_overlap_message, 'Restart instruction')
    ]
    
    print('\nValidation:')
    for check, description in checks:
        status = '✅' if check else '❌'
        print(f'{status} {description}')
