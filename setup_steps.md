# Hospital Management System Setup Steps

## 1. Install Dependencies
```bash
pip install -r requirements.txt
```

## 2. Initialize Database
Run the database initialization script to create necessary collections, indexes and test data:
```bash
python backend/scripts/init_db.py
```

This will create:
- Test users (doctor1, receptionist1, patient1)
- Database indexes
- Sample doctor, patient, and receptionist records

## 3. Start Application
Run the Flask application:
```bash
python backend/run.py
```

The application will be available at http://localhost:5000

## Test Credentials

You can log in with these test accounts:

1. Doctor Account:
   - Username: doctor1
   - Password: doctor123

2. Receptionist Account:
   - Username: receptionist1
   - Password: receptionist123

3. Patient Account:
   - Username: patient1
   - Password: patient123