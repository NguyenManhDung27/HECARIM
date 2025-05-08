from flask_login import UserMixin
from ..extensions import mongo, login_manager
from bson import ObjectId
import bcrypt

class User(UserMixin):
    def __init__(self, user_data):
        self.user_data = user_data

    @property
    def id(self):
        return str(self.user_data.get('_id'))

    @property
    def username(self):
        return self.user_data.get('username')

    @property
    def role(self):
        return self.user_data.get('role')

    @property
    def is_active(self):
        return self.user_data.get('status') == 'active'

    @staticmethod
    def get_by_id(user_id):
        try:
            user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            return User(user_data) if user_data else None
        except Exception:
            return None

    @staticmethod
    def get_by_username(username):
        user_data = mongo.db.users.find_one({'username': username})
        return User(user_data) if user_data else None

    @staticmethod
    def create_user(username, password, role, staff_id=None, patient_id=None):
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)

        user_data = {
            'username': username,
            'password_hash': password_hash,
            'role': role,
            'status': 'active',
            'permissions': get_role_permissions(role)
        }

        if staff_id:
            user_data['staff_id'] = staff_id
        if patient_id:
            user_data['patient_id'] = patient_id

        result = mongo.db.users.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        return User(user_data)

    def check_password(self, password):
        if not self.user_data.get('password_hash'):
            return False
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.user_data['password_hash']
        )

    def has_permission(self, permission):
        user_permissions = self.user_data.get('permissions', [])
        return permission in user_permissions

def get_role_permissions(role):
    """Define permissions for each role"""
    permissions = {
        'patient': [
            'view_personal_info',
            'view_appointments',
            'view_medical_history'
        ],
        'doctor': [
            'view_patient_records',
            'edit_medical_records',
            'manage_appointments',
            'prescribe_medications'
        ],
        'receptionist': [
            'register_patients',
            'manage_appointments',
            'view_billing',
            'create_invoices'
        ],
        'admin': [
            'manage_users',
            'manage_permissions',
            'view_all_records',
            'manage_system'
        ]
    }
    return permissions.get(role, [])

@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)