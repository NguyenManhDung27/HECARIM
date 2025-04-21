from flask import Blueprint, app, jsonify, redirect, render_template, url_for
from flask_login import login_required, current_user, logout_user
from datetime import datetime
from backend.app import mongo  # Import the mongo object

from backend.app.utils.api_utils import handle_api_error
from backend.app.utils.auth_utils import role_required

receptionist_bp = Blueprint('receptionist', __name__)

@receptionist_bp.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'total_appointments': 12,
        'checked_in': 5,
        'waiting': 4,
        'completed': 3
    }

    waiting_list = []
    recent_activities = []

    today = datetime.today()

    return render_template(
        'receptionist/dashboard.html',
        stats=stats,
        waiting_list=waiting_list,
        recent_activities=recent_activities,
        notifications_count=3,  # hoặc context processor như đã nói
        today=today,
    )

# @app.route('/auth/logout', methods=['POST'])
# @login_required
# def logout():
#     logout_user()
#     return redirect(url_for('auth.login'))
# @receptionist_bp.route('/api/patients', methods=['POST'])
# @login_required
# # @role_required('receptionist')
# @handle_api_error
# def create_patient():
#     print("Hàm create_patient đã được gọi!")
#     # data = request.get_json()

#     # required_fields = ['fullName', 'dateOfBirth', 'gender', 'phone', 'address']
#     # for field in required_fields:
#     #     if not data.get(field):
#     #         return api_error(f'{field} is required', 400)

#     # patient = {
#     #     'patientId': f"BN{int(datetime.now().timestamp())}",
#     #     'personalInfo': {
#     #         'fullName': data['fullName'],
#     #         'dateOfBirth': data['dateOfBirth'],
#     #         'gender': data['gender'],
#     #         'phone': data['phone'],
#     #         'address': data['address']
#     #     },
#     #     'createdAt': datetime.now(),
#     #     'updatedAt': datetime.now()
#     # }

#     # mongo.db.patients.insert_one(patient)
#     return jsonify({'message': 'Patient created successfully'})