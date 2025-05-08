import pytest
from backend.app import create_app, mongo
from datetime import datetime, timedelta
from bson import ObjectId
import json
import bcrypt

@pytest.fixture
def app():
    app = create_app('testing')
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def test_receptionist(app):
    with app.app_context():
        password = 'test123'
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        receptionist = {
            '_id': ObjectId(),
            'username': 'test_receptionist',
            'password_hash': password_hash,
            'role': 'receptionist',
            'status': 'active'
        }
        mongo.db.users.insert_one(receptionist)
        yield receptionist
        mongo.db.users.delete_one({'_id': receptionist['_id']})

@pytest.fixture
def auth_client(client, test_receptionist):
    client.post('/auth/login', json={
        'username': 'test_receptionist',
        'password': 'test123'
    })
    return client

@pytest.fixture
def department(app):
    with app.app_context():
        dept = {
            '_id': ObjectId(),
            'name': 'Test Department',
            'status': 'active'
        }
        mongo.db.departments.insert_one(dept)
        yield dept
        mongo.db.departments.delete_one({'_id': dept['_id']})

@pytest.fixture
def doctor(app, department):
    with app.app_context():
        doc = {
            '_id': ObjectId(),
            'personalInfo': {
                'fullName': 'Dr. Test'
            },
            'professionalInfo': {
                'department': department['_id']
            }
        }
        mongo.db.doctors.insert_one(doc)
        yield doc
        mongo.db.doctors.delete_one({'_id': doc['_id']})

@pytest.fixture
def patient(app):
    with app.app_context():
        pat = {
            '_id': ObjectId(),
            'patientId': 'TEST001',
            'personalInfo': {
                'fullName': 'Test Patient'
            }
        }
        mongo.db.patients.insert_one(pat)
        yield pat
        mongo.db.patients.delete_one({'_id': pat['_id']})

@pytest.fixture
def test_appointments(app, doctor, patient):
    with app.app_context():
        appointments = []
        now = datetime.now()
        
        # Create appointments with different statuses
        statuses = ['scheduled', 'confirmed', 'checked_in', 'completed', 'cancelled']
        for i, status in enumerate(statuses):
            appt = {
                '_id': ObjectId(),
                'patientId': patient['_id'],
                'doctorId': doctor['_id'],
                'timeSlot': {
                    'start': now + timedelta(hours=i),
                    'end': now + timedelta(hours=i+1)
                },
                'type': 'regular',
                'status': status,
                'createdAt': now,
                'updatedAt': now
            }
            mongo.db.appointments.insert_one(appt)
            appointments.append(appt)
        
        yield appointments
        
        # Cleanup
        appointment_ids = [appt['_id'] for appt in appointments]
        mongo.db.appointments.delete_many({'_id': {'$in': appointment_ids}})

def test_list_appointments(auth_client, test_appointments):
    response = auth_client.get('/receptionist/api/appointments')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    assert 'appointments' in data
    assert len(data['appointments']) == 5
    assert 'total_pages' in data
    assert 'current_page' in data
    assert 'total_items' in data

def test_list_appointments_with_filters(auth_client, test_appointments, department):
    # Test date filter
    today = datetime.now().strftime('%Y-%m-%d')
    response = auth_client.get(f'/receptionist/api/appointments?date={today}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['appointments']) == 5

    # Test status filter
    response = auth_client.get('/receptionist/api/appointments?status=scheduled')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['appointments']) == 1
    assert data['appointments'][0]['status'] == 'scheduled'

    # Test department filter
    response = auth_client.get(f'/receptionist/api/appointments?department={str(department["_id"])}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['appointments']) > 0

def test_list_appointments_with_search(auth_client, test_appointments, patient):
    # Search by patient name
    response = auth_client.get('/receptionist/api/appointments?search=Test Patient')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['appointments']) > 0

    # Search by patient ID
    response = auth_client.get('/receptionist/api/appointments?search=TEST001')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data['appointments']) > 0

def test_get_appointment_details(auth_client, test_appointments):
    appt_id = str(test_appointments[0]['_id'])
    response = auth_client.get(f'/receptionist/api/appointments/{appt_id}')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['id'] == appt_id
    assert 'patientName' in data
    assert 'doctorName' in data
    assert 'timeSlot' in data
    assert 'status' in data

def test_update_appointment_status(auth_client, test_appointments):
    appt_id = str(test_appointments[0]['_id'])
    
    # Test valid status update
    response = auth_client.post(
        f'/receptionist/api/appointments/{appt_id}/status',
        json={'status': 'confirmed'}
    )
    assert response.status_code == 200
    
    # Verify status was updated
    with auth_client.application.app_context():
        appointment = mongo.db.appointments.find_one({'_id': ObjectId(appt_id)})
        assert appointment['status'] == 'confirmed'

def test_invalid_status_update(auth_client, test_appointments):
    appt_id = str(test_appointments[0]['_id'])
    
    # Test invalid status
    response = auth_client.post(
        f'/receptionist/api/appointments/{appt_id}/status',
        json={'status': 'invalid_status'}
    )
    assert response.status_code == 400
    
    # Test updating completed appointment
    completed_appt = next(a for a in test_appointments if a['status'] == 'completed')
    response = auth_client.post(
        f'/receptionist/api/appointments/{str(completed_appt["_id"])}/status',
        json={'status': 'confirmed'}
    )
    assert response.status_code == 400

@pytest.fixture(autouse=True)
def cleanup(app):
    yield
    with app.app_context():
        collections = ['appointments', 'doctors', 'patients', 'departments', 'users']
        for collection in collections:
            mongo.db[collection].delete_many({})