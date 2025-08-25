import pytest
from app import create_app, db
from app.models.planner import Planner
from app.models.event import Event

@pytest.fixture
def app():
    """Create and configure a test app."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

def test_app_creation(app):
    """Test that the app is created successfully."""
    assert app is not None

def test_planner_creation(app):
    """Test planner model creation."""
    with app.app_context():
        planner = Planner(phone_number='1234567890', name='Test User')
        planner.save()
        
        found_planner = Planner.query.filter_by(phone_number='1234567890').first()
        assert found_planner is not None
        assert found_planner.name == 'Test User'

def test_sms_test_endpoint(client):
    """Test the SMS test endpoint."""
    response = client.post('/sms/test', json={
        'phone_number': '1234567890',
        'message': 'Hello'
    })
    
    assert response.status_code == 200
    assert 'response' in response.get_json()
