import pytest
import json
from app import create_app, db
from app.models.planner import Planner
from app.models.event import Event
from app.models.guest import Guest

def test_complete_sms_workflow():
    """Test the complete SMS workflow from start to finish."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        
        client = app.test_client()
        phone = "5551234567"
        
        # Step 1: New user - should ask for name
        response = client.post('/sms/test', json={
            'phone_number': phone,
            'message': 'Hello'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert "What's your name?" in data['response']
        
        # Step 2: Provide name - should move to event creation
        response = client.post('/sms/test', json={
            'phone_number': phone,
            'message': 'Aaron'
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert "Great to meet you, Aaron!" in data['response']
        assert "Who's coming?" in data['response']
        
        # Verify planner was created
        planner = Planner.query.filter_by(phone_number=phone).first()
        assert planner is not None
        assert planner.name == 'Aaron'
        
        # Step 3: Add guest
        response = client.post('/sms/test', json={
            'phone_number': phone,
            'message': 'John Doe, 555-0123'
        })
        
        print("Guest addition response:", response.get_json())
        
        # Step 4: Finish adding guests
        response = client.post('/sms/test', json={
            'phone_number': phone,
            'message': 'done'
        })
        
        print("Done response:", response.get_json())
        
        # Step 5: Add dates
        response = client.post('/sms/test', json={
            'phone_number': phone,
            'message': 'Monday'
        })
        
        print("Date response:", response.get_json())
        
        db.drop_all()

if __name__ == "__main__":
    test_complete_sms_workflow()
