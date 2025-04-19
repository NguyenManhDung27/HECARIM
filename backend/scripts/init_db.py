from pymongo import MongoClient
from datetime import datetime
import bcrypt
from bson import ObjectId
import os
import sys

# MongoDB connection with authentication options
def get_db():
    try:
        client = MongoClient(
            'mongodb://localhost:27017/',
            serverSelectionTimeoutMS=5000  # 5 second timeout
        )
        # Test the connection
        client.admin.command('ping')
        print("Successfully connected to MongoDB")
        return client['hospital_management']
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        sys.exit(1)

def create_indexes(db):
    """Create necessary indexes for collections"""
    try:
        # Users collection indexes
        db.users.create_index('username', unique=True)
        db.users.create_index('staff_id')
        
        # Patients collection indexes
        db.patients.create_index('patientId', unique=True)
        db.patients.create_index('personalInfo.idNumber', unique=True)
        
        # Doctors collection indexes
        db.doctors.create_index('doctorId', unique=True)
        db.doctors.create_index('personalInfo.idNumber', unique=True)
        
        # Appointments collection indexes
        db.appointments.create_index([('patientId', 1), ('appointmentDate', 1)])
        db.appointments.create_index([('doctorId', 1), ('appointmentDate', 1)])
        
        print("Successfully created all indexes")
    except Exception as e:
        print(f"Error creating indexes: {e}")
        sys.exit(1)

def create_test_data(db):
    """Create initial test data"""
    try:
        # Clear existing data
        collections = ['users', 'patients', 'doctors', 'receptionists', 'appointments']
        for collection in collections:
            db[collection].delete_many({})

        # Create a test doctor
        doctor_id = ObjectId()
        doctor = {
            '_id': doctor_id,
            'doctorId': 'DOC001',
            'personalInfo': {
                'fullName': 'Nguyễn Văn A',
                'gender': 'Nam',
                'dateOfBirth': datetime(1980, 1, 1),
                'idNumber': '123456789',
                'address': 'Hà Nội',
                'phone': '0123456789',
                'email': 'doctor@example.com'
            },
            'professionalInfo': {
                'specialization': 'Nội khoa',
                'qualification': ['Bác sĩ chuyên khoa I'],
                'licenseNumber': 'LICENSE001',
                'experience': 10,
                'department': 'Khoa Nội'
            },
            'schedule': {
                'workDays': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                'workHours': {
                    'start': '08:00',
                    'end': '17:00'
                }
            },
            'createdAt': datetime.now(),
            'updatedAt': datetime.now()
        }
        db.doctors.insert_one(doctor)

        # Create a test receptionist
        receptionist_id = ObjectId()
        receptionist = {
            '_id': receptionist_id,
            'staffId': 'REC001',
            'personalInfo': {
                'fullName': 'Trần Thị B',
                'gender': 'Nữ',
                'dateOfBirth': datetime(1990, 1, 1),
                'idNumber': '987654321',
                'address': 'Hà Nội',
                'phone': '0987654321',
                'email': 'receptionist@example.com'
            },
            'employmentInfo': {
                'joinDate': datetime(2020, 1, 1),
                'shift': 'Ca sáng',
                'status': 'Đang làm việc'
            },
            'createdAt': datetime.now(),
            'updatedAt': datetime.now()
        }
        db.receptionists.insert_one(receptionist)

        # Create a test patient
        patient_id = ObjectId()
        patient = {
            '_id': patient_id,
            'patientId': 'PAT001',
            'personalInfo': {
                'fullName': 'Lê Văn C',
                'gender': 'Nam',
                'dateOfBirth': datetime(1995, 1, 1),
                'idNumber': '456789123',
                'address': 'Hà Nội',
                'phone': '0345678912',
                'email': 'patient@example.com'
            },
            'healthInfo': {
                'bloodType': 'A+',
                'allergies': [],
                'chronicDiseases': [],
                'height': 170,
                'weight': 65
            },
            'createdAt': datetime.now(),
            'updatedAt': datetime.now()
        }
        db.patients.insert_one(patient)

        # Create user accounts
        test_users = [
            {
                'username': 'doctor1',
                'password': 'doctor123',
                'role': 'doctor',
                'staff_id': doctor_id
            },
            {
                'username': 'receptionist1',
                'password': 'receptionist123',
                'role': 'receptionist',
                'staff_id': receptionist_id
            },
            {
                'username': 'patient1',
                'password': 'patient123',
                'role': 'patient',
                'patient_id': patient_id
            }
        ]

        for user in test_users:
            password = user.pop('password')
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
            user['password_hash'] = password_hash
            user['status'] = 'active'
            user['createdAt'] = datetime.now()
            user['updatedAt'] = datetime.now()
            db.users.insert_one(user)

        print("Successfully created test data")
    except Exception as e:
        print(f"Error creating test data: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print("Connecting to MongoDB...")
    db = get_db()
    
    print("Creating database indexes...")
    create_indexes(db)
    
    print("Creating test data...")
    create_test_data(db)
    
    print("Database initialization completed successfully!")