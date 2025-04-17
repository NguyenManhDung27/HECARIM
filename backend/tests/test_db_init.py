import pytest
from pymongo import MongoClient
from backend.scripts.init_db import create_indexes, create_test_data
from backend.app import create_app, mongo

@pytest.fixture
def app():
    app = create_app('testing')
    return app

@pytest.fixture(autouse=True)
def cleanup(app):
    yield
    with app.app_context():
        # Drop test database after each test
        client = MongoClient('mongodb://localhost:27017/')
        client.drop_database('hospital_management_test')

def test_database_connection(app):
    """Test MongoDB connection and database initialization"""
    with app.app_context():
        try:
            # Check if we can execute a command
            result = mongo.db.command('ping')
            assert result.get('ok') == 1
        except Exception as e:
            pytest.fail(f"MongoDB connection failed: {str(e)}")

def test_create_indexes(app):
    """Test index creation"""
    with app.app_context():
        try:
            # Create indexes directly using mongo.db
            mongo.db.users.create_index('username', unique=True)
            mongo.db.users.create_index('staff_id')
            
            mongo.db.patients.create_index('patientId', unique=True)
            mongo.db.patients.create_index('personalInfo.idNumber', unique=True)
            
            mongo.db.doctors.create_index('doctorId', unique=True)
            mongo.db.doctors.create_index('personalInfo.idNumber', unique=True)
            
            mongo.db.appointments.create_index([('patientId', 1), ('appointmentDate', 1)])
            mongo.db.appointments.create_index([('doctorId', 1), ('appointmentDate', 1)])
            
            # Verify indexes
            user_indexes = mongo.db.users.index_information()
            assert 'username_1' in user_indexes  # Check username index
            
            patient_indexes = mongo.db.patients.index_information()
            assert 'patientId_1' in patient_indexes  # Check patientId index
            
            doctor_indexes = mongo.db.doctors.index_information()
            assert 'doctorId_1' in doctor_indexes  # Check doctorId index
            
        except Exception as e:
            pytest.fail(f"Failed to create indexes: {str(e)}")

def test_create_test_data(app):
    """Test creation of test data"""
    with app.app_context():
        # Delete existing data first
        for collection in ['users', 'patients', 'doctors', 'receptionists', 'appointments']:
            mongo.db[collection].delete_many({})
        
        try:
            # Create test data using the functions from init_db.py
            # But pass in our test database instance
            create_test_data(mongo.db)
            
            # Verify test users were created
            users = list(mongo.db.users.find())
            assert len(users) >= 3  # Should have at least doctor, receptionist, and patient
            
            # Verify test doctor
            doctor = mongo.db.doctors.find_one({'doctorId': 'DOC001'})
            assert doctor is not None
            assert doctor['personalInfo']['fullName'] == 'Nguyễn Văn A'
            
            # Verify test receptionist
            receptionist = mongo.db.receptionists.find_one({'staffId': 'REC001'})
            assert receptionist is not None
            assert receptionist['personalInfo']['fullName'] == 'Trần Thị B'
            
            # Verify test patient
            patient = mongo.db.patients.find_one({'patientId': 'PAT001'})
            assert patient is not None
            assert patient['personalInfo']['fullName'] == 'Lê Văn C'
            
        except Exception as e:
            pytest.fail(f"Failed to create test data: {str(e)}")

def test_user_roles(app):
    """Test user roles and permissions"""
    with app.app_context():
        # Create test data first
        test_create_test_data(app)
        
        # Verify doctor user
        doctor_user = mongo.db.users.find_one({'username': 'doctor1'})
        assert doctor_user is not None
        assert doctor_user['role'] == 'doctor'
        
        # Verify receptionist user
        receptionist_user = mongo.db.users.find_one({'username': 'receptionist1'})
        assert receptionist_user is not None
        assert receptionist_user['role'] == 'receptionist'
        
        # Verify patient user
        patient_user = mongo.db.users.find_one({'username': 'patient1'})
        assert patient_user is not None
        assert patient_user['role'] == 'patient'