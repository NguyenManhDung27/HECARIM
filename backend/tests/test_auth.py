import pytest
from backend.app import create_app, mongo
from backend.app.models.user import User
import json

@pytest.fixture
def app():
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User.create_user(
            username='test_patient',
            password='test123',
            role='patient'
        )
        yield user
        # Cleanup after test
        mongo.db.users.delete_many({})

def test_login_success(client, test_user):
    response = client.post('/auth/login', json={
        'username': 'test_patient',
        'password': 'test123'
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data
    assert 'user' in data
    assert data['user']['username'] == 'test_patient'
    assert data['user']['role'] == 'patient'

def test_login_invalid_credentials(client):
    response = client.post('/auth/login', json={
        'username': 'nonexistent',
        'password': 'wrong'
    })
    
    assert response.status_code == 401
    data = json.loads(response.data)
    assert 'error' in data

def test_register_patient(client):
    response = client.post('/auth/register', json={
        'username': 'new_patient',
        'password': 'patient123',
        'role': 'patient'
    })
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'message' in data
    assert 'user' in data
    assert data['user']['username'] == 'new_patient'
    assert data['user']['role'] == 'patient'

def test_register_duplicate_username(client, test_user):
    # Try to register with existing username
    response = client.post('/auth/register', json={
        'username': 'test_patient',
        'password': 'test123',
        'role': 'patient'
    })
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'already exists' in data['error'].lower()

def test_logout(client, test_user):
    # Login first
    client.post('/auth/login', json={
        'username': 'test_patient',
        'password': 'test123'
    })
    
    # Test logout
    response = client.post('/auth/logout')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data

def test_get_current_user(client, test_user):
    # Login first
    client.post('/auth/login', json={
        'username': 'test_patient',
        'password': 'test123'
    })
    
    # Test get current user
    response = client.get('/auth/me')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'user' in data
    assert data['user']['username'] == 'test_patient'

@pytest.fixture(autouse=True)
def cleanup(app):
    # This will run after each test function
    yield
    with app.app_context():
        mongo.db.users.delete_many({})