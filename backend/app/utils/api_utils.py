from flask import jsonify
from bson.errors import InvalidId
from pymongo.errors import PyMongoError

def api_error(message, status_code=400):
    """Return a JSON error response with the given message and status code"""
    response = jsonify({'error': message})
    response.status_code = status_code
    return response

def handle_api_error(func):
    """Decorator to handle common API errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except InvalidId:
            return api_error('Invalid ID format', 400)
        except PyMongoError as e:
            return api_error(f'Database error: {str(e)}', 500)
        except ValueError as e:
            return api_error(str(e), 400)
        except Exception as e:
            return api_error(f'Internal server error: {str(e)}', 500)
    wrapper.__name__ = func.__name__
    return wrapper

def validate_appointment_data(data):
    """Validate appointment data and return validated data or raise ValueError"""
    required_fields = ['patientId', 'doctorId', 'appointmentDate', 'timeSlot', 'type']
    
    # Check required fields
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Validate appointment type
    valid_types = ['regular', 'follow_up', 'emergency']
    if data['type'] not in valid_types:
        raise ValueError(f"Invalid appointment type. Must be one of: {', '.join(valid_types)}")
    
    # Time slot format should be HH:MM
    time = data['timeSlot']
    if not isinstance(time, str) or not len(time) == 5 or not time[2] == ':':
        raise ValueError("Time slot must be in format HH:MM")
    
    try:
        hour, minute = map(int, time.split(':'))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except ValueError:
        raise ValueError("Invalid time format")
    
    return data

def format_appointment_response(appointment):
    """Format appointment data for API response"""
    return {
        'id': str(appointment['_id']),
        'patientId': str(appointment['patientId']),
        'doctorId': str(appointment['doctorId']),
        'timeSlot': {
            'start': appointment['timeSlot']['start'].strftime('%Y-%m-%d %H:%M'),
            'end': appointment['timeSlot']['end'].strftime('%Y-%m-%d %H:%M')
        },
        'type': appointment['type'],
        'status': appointment['status'],
        'reason': appointment.get('reason', ''),
        'notes': appointment.get('notes', ''),
        'createdAt': appointment['createdAt'].strftime('%Y-%m-%d %H:%M:%S'),
        'updatedAt': appointment['updatedAt'].strftime('%Y-%m-%d %H:%M:%S')
    }

def format_doctor_response(doctor):
    """Format doctor data for API response"""
    return {
        'id': str(doctor['_id']),
        'name': doctor['personalInfo']['fullName'],
        'specialization': doctor['professionalInfo']['specialization'],
        'department': str(doctor['professionalInfo']['department'])
    }

def format_patient_response(patient):
    """Format patient data for API response"""
    return {
        'id': str(patient['_id']),
        'patientId': patient['patientId'],
        'name': patient['personalInfo']['fullName'],
        'dateOfBirth': patient['personalInfo']['dateOfBirth'].strftime('%d/%m/%Y'),
        'phone': patient['personalInfo']['phone']
    }