from flask import Blueprint, render_template, request, redirect, url_for, flash, g
from flask_login import login_user, logout_user, login_required, current_user
from ..models.user import User
from ..extensions import mongo
import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        elif current_user.role == 'receptionist':
            return redirect(url_for('receptionist.dashboard'))
        elif current_user.role == 'patient':
            return redirect(url_for('patient.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        user = User.get_by_username(username)
        
        if user and user.check_password(password) and user.role == role:
            login_user(user)
            if role == 'doctor':
                return redirect(url_for('doctor.dashboard'))
            elif role == 'receptionist':
                return redirect(url_for('receptionist.dashboard'))
            elif role == 'patient':
                return redirect(url_for('patient.dashboard'))
        
        flash('Sai tên đăng nhập hoặc mật khẩu', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    if current_user.role == 'doctor':
        doctor_info = mongo.db.doctors.find_one({'_id': current_user.user_data.get('staff_id')})
        return render_template('auth/profile.html',
                          personal_info=doctor_info['personalInfo'],
                          doctor=doctor_info)
    elif current_user.role == 'receptionist':
        receptionist_info = mongo.db.receptionists.find_one({'_id': current_user.user_data.get('staff_id')})
        return render_template('auth/profile.html',
                          personal_info=receptionist_info['personalInfo'])
    else:
        patient_info = mongo.db.patients.find_one({'_id': current_user.user_data.get('patient_id')})
        return render_template('auth/profile.html',
                          personal_info=patient_info['personalInfo'])

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_user.check_password(current_password):
        return {'success': False, 'message': 'Mật khẩu hiện tại không đúng'}

    # Update password in database
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(new_password.encode('utf-8'), salt)
    
    mongo.db.users.update_one(
        {'_id': current_user.id},
        {'$set': {'password_hash': password_hash}}
    )

    return {'success': True}

@auth_bp.route('/update-settings', methods=['POST'])
@login_required
def update_settings():
    data = request.get_json()
    setting = data.get('setting')
    value = data.get('value')

    mongo.db.users.update_one(
        {'_id': current_user.id},
        {'$set': {setting: value}}
    )

    return {'success': True}

@auth_bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        # Get notifications count
        notifications = mongo.db.notifications.count_documents({
            'user_id': current_user.id,
            'read': False
        })
        g.notifications_count = notifications
    else:
        g.notifications_count = 0

@auth_bp.context_processor
def inject_notifications_count():
    return {'notifications_count': getattr(g, 'notifications_count', 0)}