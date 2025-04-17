from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from backend.app.models.user import User
from backend.app import mongo
from bson import ObjectId

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return jsonify({'message': 'Already logged in'}), 400

    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400

    user = User.get_by_username(username)
    if user and user.check_password(password):
        if not user.is_active:
            return jsonify({'error': 'Account is disabled'}), 403
        
        login_user(user)
        return jsonify({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        })
    
    return jsonify({'error': 'Invalid username or password'}), 401

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logout successful'})

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    required_fields = ['username', 'password', 'role']
    
    # Validate required fields
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    username = data['username']
    password = data['password']
    role = data['role']
    staff_id = data.get('staff_id')  # Optional for doctors and receptionists

    # Validate role
    valid_roles = ['patient', 'doctor', 'receptionist']
    if role not in valid_roles:
        return jsonify({'error': 'Invalid role'}), 400

    # Check if username already exists
    if User.get_by_username(username):
        return jsonify({'error': 'Username already exists'}), 400

    # Validate staff_id for doctors and receptionists
    if role in ['doctor', 'receptionist']:
        if not staff_id:
            return jsonify({'error': f'Staff ID required for {role} role'}), 400
        
        # Verify staff exists in respective collection
        collection = 'doctors' if role == 'doctor' else 'receptionists'
        staff = mongo.db[collection].find_one({'_id': ObjectId(staff_id)})
        if not staff:
            return jsonify({'error': f'Invalid {role} ID'}), 400

    # Create new user
    try:
        user = User.create_user(
            username=username,
            password=password,
            role=role,
            staff_id=staff_id
        )
        return jsonify({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        }), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    return jsonify({
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'role': current_user.role
        }
    })

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({'error': 'Missing password fields'}), 400

    if not current_user.check_password(current_password):
        return jsonify({'error': 'Current password is incorrect'}), 401

    # Update password
    try:
        mongo.db.users.update_one(
            {'_id': ObjectId(current_user.id)},
            {'$set': {'password_hash': User.create_user.password_hash(new_password)}}
        )
        return jsonify({'message': 'Password updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500