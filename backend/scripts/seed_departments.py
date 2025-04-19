from pymongo import MongoClient
from datetime import datetime

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['hospital_management']

# List of departments
departments = [
    {
        'name': 'Khoa Nội',
        'description': 'Khám và điều trị các bệnh nội khoa',
        'status': 'active',
        'createdAt': datetime.now(),
        'updatedAt': datetime.now()
    },
    {
        'name': 'Khoa Ngoại',
        'description': 'Khám và điều trị các bệnh ngoại khoa',
        'status': 'active',
        'createdAt': datetime.now(),
        'updatedAt': datetime.now()
    },
    {
        'name': 'Khoa Sản',
        'description': 'Khám và điều trị các bệnh phụ khoa, thai sản',
        'status': 'active',
        'createdAt': datetime.now(),
        'updatedAt': datetime.now()
    },
    {
        'name': 'Khoa Nhi',
        'description': 'Khám và điều trị bệnh cho trẻ em',
        'status': 'active',
        'createdAt': datetime.now(),
        'updatedAt': datetime.now()
    },
    {
        'name': 'Khoa Tim mạch',
        'description': 'Khám và điều trị các bệnh về tim mạch',
        'status': 'active',
        'createdAt': datetime.now(),
        'updatedAt': datetime.now()
    },
    {
        'name': 'Khoa Thần kinh',
        'description': 'Khám và điều trị các bệnh về thần kinh',
        'status': 'active',
        'createdAt': datetime.now(),
        'updatedAt': datetime.now()
    }
]

# Insert departments
try:
    # Clear existing departments
    db.departments.delete_many({})
    
    # Insert new departments
    result = db.departments.insert_many(departments)
    print(f'Successfully created {len(result.inserted_ids)} departments')
    
    # Update doctor test data to use real department IDs
    first_dept_id = result.inserted_ids[0]
    db.doctors.update_many(
        {'professionalInfo.department': {'$exists': True}},
        {'$set': {'professionalInfo.department': first_dept_id}}
    )
    print('Updated test doctors with real department ID')
    
except Exception as e:
    print(f'Error seeding departments: {str(e)}')