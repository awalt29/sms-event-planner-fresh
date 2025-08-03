import unittest
from app import create_app
from app.models import db, Planner, Event
from app.config import TestingConfig


class TestPlannerModel(unittest.TestCase):
    
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_create_planner(self):
        planner = Planner(
            phone_number='+15551234567',
            name='Test Planner'
        )
        planner.save()
        
        self.assertIsNotNone(planner.id)
        self.assertEqual(planner.phone_number, '+15551234567')
        self.assertEqual(planner.name, 'Test Planner')
    
    def test_planner_preferences(self):
        planner = Planner(phone_number='+15551234567')
        
        # Test empty preferences
        self.assertEqual(planner.get_preferences(), {})
        
        # Test setting preferences
        prefs = {'timezone': 'America/New_York', 'notifications': True}
        planner.set_preferences(prefs)
        planner.save()
        
        self.assertEqual(planner.get_preferences(), prefs)


class TestEventModel(unittest.TestCase):
    
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test planner
        self.planner = Planner(
            phone_number='+15551234567',
            name='Test Planner'
        )
        self.planner.save()
    
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_create_event(self):
        event = Event(
            planner_id=self.planner.id,
            title='Test Event',
            description='A test event',
            activity='Birthday Party',
            location='Downtown'
        )
        event.save()
        
        self.assertIsNotNone(event.id)
        self.assertEqual(event.title, 'Test Event')
        self.assertEqual(event.planner_id, self.planner.id)
        self.assertEqual(event.status, 'planning')  # default status
    
    def test_event_venue_info(self):
        event = Event(
            planner_id=self.planner.id,
            title='Test Event'
        )
        
        # Test empty venue info
        self.assertEqual(event.get_venue_info(), {})
        
        # Test setting venue info
        venue_info = {
            'name': 'Test Venue',
            'address': '123 Main St',
            'capacity': 50
        }
        event.set_venue_info(venue_info)
        event.save()
        
        self.assertEqual(event.get_venue_info(), venue_info)


if __name__ == '__main__':
    unittest.main()
