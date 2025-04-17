from functools import wraps
from flask import jsonify
from flask_login import current_user

def role_required(*roles):
    """
    Decorator to check if current user has required role
    Usage: @role_required('doctor', 'admin')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            if current_user.role not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def permission_required(permission):
    """
    Decorator to check if current user has required permission
    Usage: @permission_required('manage_appointments')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({'error': 'Authentication required'}), 401
            
            if not current_user.has_permission(permission):
                return jsonify({'error': 'Insufficient permissions'}), 403
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_user_access(user_id):
    """
    Utility function to check if current user has access to requested user data
    Returns True if:
    - Current user is accessing their own data
    - Current user is a doctor or receptionist with appropriate permissions
    """
    if str(current_user.id) == str(user_id):
        return True
        
    if current_user.role in ['doctor', 'receptionist', 'admin']:
        if current_user.has_permission('view_all_records'):
            return True
            
    return False

def get_current_user_data():
    """
    Utility function to get current user's complete data including role-specific information
    """
    if not current_user.is_authenticated:
        return None
        
    user_data = {
        'id': current_user.id,
        'username': current_user.username,
        'role': current_user.role
    }
    
    # Add role-specific data
    if current_user.role == 'doctor':
        doctor = mongo.db.doctors.find_one({'_id': ObjectId(current_user.user_data.get('staff_id'))})
        if doctor:
            user_data['doctor_info'] = {
                'name': doctor.get('personalInfo', {}).get('fullName'),
                'specialization': doctor.get('professionalInfo', {}).get('specialization'),
                'department': doctor.get('professionalInfo', {}).get('department')
            }
            
    elif current_user.role == 'receptionist':
        receptionist = mongo.db.receptionists.find_one({'_id': ObjectId(current_user.user_data.get('staff_id'))})
        if receptionist:
            user_data['receptionist_info'] = {
                'name': receptionist.get('personalInfo', {}).get('fullName'),
                'shift': receptionist.get('employmentInfo', {}).get('shift')
            }
            
    elif current_user.role == 'patient':
        patient = mongo.db.patients.find_one({'_id': ObjectId(current_user.user_data.get('patient_id'))})
        if patient:
            user_data['patient_info'] = {
                'name': patient.get('personalInfo', {}).get('fullName'),
                'patientId': patient.get('patientId')
            }
            
    return user_data