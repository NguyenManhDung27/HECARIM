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
        # Create a test receptionist user
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
    # Log in the test receptionist
    client.post('/auth/login', json={
        'username': 'test_receptionist',
        'password': 'test123'
    })
    return client

@pytest.fixture
def test_department(app):
    with app.app_context():
        department = {
            '_id': ObjectId(),
            'name': 'Test Department',
            'status': 'active'
        }
        mongo.db.departments.insert_one(department)
        yield department
        mongo.db.departments.delete_one({'_id': department['_id']})

@pytest.fixture
def test_doctor(app, test_department):
    with app.app_context():
        doctor = {
            '_id': ObjectId(),
            'doctorId': 'DOC_TEST',
            'personalInfo': {
                'fullName': 'Dr. Test',
                'gender': 'Nam',
                'dateOfBirth': datetime(1980, 1, 1),
                'idNumber': '123456789',
                'address': 'Test Address',
                'phone': '0123456789',
                'email': 'test.doctor@example.com'
            },
            'professionalInfo': {
                'specialization': 'Test Specialization',
                'department': test_department['_id'],
                'licenseNumber': 'TEST123'
            },
            'schedule': {
                'workDays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'workHours': {
                    'start': '08:00',
                    'end': '17:00'
                }
            },
            'status': 'active'
        }
        mongo.db.doctors.insert_one(doctor)
        yield doctor
        mongo.db.doctors.delete_one({'_id': doctor['_id']})

@pytest.fixture
def test_patient(app):
    with app.app_context():
        patient = {
            '_id': ObjectId(),
            'patientId': 'PAT_TEST',
            'personalInfo': {
                'fullName': 'Test Patient',
                'gender': 'Nam',
                'dateOfBirth': datetime(1990, 1, 1),
                'idNumber': '987654321',
                'address': 'Test Address',
                'phone': '0987654321',
                'email': 'test.patient@example.com'
            }
        }
        mongo.db.patients.insert_one(patient)
        yield patient
        mongo.db.patients.delete_one({'_id': patient['_id']})

# Basic functionality tests
def test_search_patients(auth_client, test_patient):
    response = auth_client.get('/receptionist/api/search-patients?q=test')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) >= 1
    assert any(p['patientId'] == 'PAT_TEST' for p in data)

def test_get_doctors(auth_client, test_doctor, test_department):
    response = auth_client.get(f'/receptionist/api/doctors?department={str(test_department["_id"])}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) >= 1
    assert any(d['name'] == 'Dr. Test' for d in data)

def test_get_time_slots(auth_client, test_doctor):
    tomorrow = datetime.now() + timedelta(days=1)
    date_str = tomorrow.strftime('%Y-%m-%d')
    response = auth_client.get(f'/receptionist/api/time-slots?date={date_str}&doctor={str(test_doctor["_id"])}')
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) > 0
    assert all('value' in slot and 'label' in slot for slot in data)

def test_create_appointment(auth_client, test_doctor, test_patient):
    tomorrow = datetime.now() + timedelta(days=1)
    appointment_data = {
        'patientId': str(test_patient['_id']),
        'doctorId': str(test_doctor['_id']),
        'appointmentDate': tomorrow.strftime('%Y-%m-%d'),
        'timeSlot': '09:00',
        'type': 'regular',
        'reason': 'Test appointment',
        'notes': 'Test notes'
    }

    response = auth_client.post('/receptionist/api/appointments',
                              json=appointment_data,
                              content_type='application/json')
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'appointmentId' in data
    assert 'appointment' in data
    
    # Verify appointment was created
    with auth_client.application.app_context():
        appointment = mongo.db.appointments.find_one({'_id': ObjectId(data['appointmentId'])})
        assert appointment is not None
        assert appointment['type'] == 'regular'
        assert appointment['status'] == 'scheduled'

def test_create_duplicate_appointment(auth_client, test_doctor, test_patient):
    # First appointment
    tomorrow = datetime.now() + timedelta(days=1)
    appointment_data = {
        'patientId': str(test_patient['_id']),
        'doctorId': str(test_doctor['_id']),
        'appointmentDate': tomorrow.strftime('%Y-%m-%d'),
        'timeSlot': '10:00',
        'type': 'regular'
    }

    # Create first appointment
    response = auth_client.post('/receptionist/api/appointments',
                              json=appointment_data,
                              content_type='application/json')
    assert response.status_code == 201

    # Try to create another appointment at the same time
    response = auth_client.post('/receptionist/api/appointments',
                              json=appointment_data,
                              content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'no longer available' in data['error'].lower()

# Error handling tests
def test_invalid_patient_id(auth_client, test_doctor):
    tomorrow = datetime.now() + timedelta(days=1)
    appointment_data = {
        'patientId': 'invalid_id',
        'doctorId': str(test_doctor['_id']),
        'appointmentDate': tomorrow.strftime('%Y-%m-%d'),
        'timeSlot': '09:00',
        'type': 'regular'
    }

    response = auth_client.post('/receptionist/api/appointments',
                              json=appointment_data,
                              content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'invalid id format' in data['error'].lower()

def test_invalid_time_slot(auth_client, test_doctor, test_patient):
    tomorrow = datetime.now() + timedelta(days=1)
    appointment_data = {
        'patientId': str(test_patient['_id']),
        'doctorId': str(test_doctor['_id']),
        'appointmentDate': tomorrow.strftime('%Y-%m-%d'),
        'timeSlot': '25:00',  # Invalid time
        'type': 'regular'
    }

    response = auth_client.post('/receptionist/api/appointments',
                              json=appointment_data,
                              content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'invalid time format' in data['error'].lower()

def test_invalid_appointment_type(auth_client, test_doctor, test_patient):
    tomorrow = datetime.now() + timedelta(days=1)
    appointment_data = {
        'patientId': str(test_patient['_id']),
        'doctorId': str(test_doctor['_id']),
        'appointmentDate': tomorrow.strftime('%Y-%m-%d'),
        'timeSlot': '09:00',
        'type': 'invalid_type'  # Invalid appointment type
    }

    response = auth_client.post('/receptionist/api/appointments',
                              json=appointment_data,
                              content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data
    assert 'invalid appointment type' in data['error'].lower()

@pytest.fixture(autouse=True)
def cleanup(app):
    yield
    with app.app_context():
        # Clean up test database after each test
        mongo.db.appointments.delete_many({})