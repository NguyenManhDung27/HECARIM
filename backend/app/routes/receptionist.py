from bson import ObjectId
from flask import Blueprint, app, jsonify, redirect, render_template, url_for
from flask_login import login_required, current_user, logout_user
from datetime import datetime, timedelta
from backend.app import mongo  # Import the mongo object

from backend.app.utils.api_utils import handle_api_error
from backend.app.utils.auth_utils import role_required

receptionist_bp = Blueprint('receptionist', __name__)

@receptionist_bp.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'total_appointments': 0,
        'checked_in': 0,
        'waiting': 0,
        'completed': 0
    }
    today = datetime.today()
    current_user_id = str(current_user.id)  # Lấy ID người dùng hiện tại
    waiting_list = []
    recent_activities = []
    start_of_day = datetime.combine(today.date(), datetime.min.time())
    end_of_day = datetime.combine(today.date(), datetime.max.time())
    appointments = mongo.db.appointments.find({
        'appointmentTime': {'$gte': start_of_day, '$lte': end_of_day},
    })
    for appt in appointments:
        # Lấy thông tin bệnh nhân
        patient = mongo.db.patients.find_one({'_id': ObjectId(appt['patientId'])})
        doctor = mongo.db.doctors.find_one({'_id': ObjectId(appt['doctorId'])})

        # An toàn khi truy xuất thông tin
        patient_name = patient['personalInfo']['fullName'] if patient else 'Không rõ'
        doctor_name = doctor['personalInfo']['fullName'] if doctor else 'Không rõ'

        status_class = 'success' if appt.get('status') == "đã check-in" else 'warning'  # hoặc tạo rule cho status_class theo trạng thái
        check_in_time_str = appt.get('timeSlot')  # Giả sử timeSlot là chuỗi thời gian

    # Chuyển đổi check_in_time từ chuỗi sang datetime
        check_in_time = None
        if check_in_time_str:
            try:
            # Xử lý định dạng HH:mm
                check_in_time = datetime.combine(
                today.date(),  # Kết hợp với ngày hiện tại
                datetime.strptime(check_in_time_str, '%H:%M').time()  # Chuyển đổi chuỗi HH:mm thành đối tượng time
                )
            except ValueError:
                print(f"Invalid time format: {check_in_time_str}")

    # Kiểm tra trạng thái và thời gian check-in
        # So sánh với giờ trước 1 tiếng hiện tại
        one_hour_ago = datetime.now() - timedelta(hours=1)
        if appt.get('status') == "đã check-in":
            if check_in_time and check_in_time < one_hour_ago:
                stats['completed'] += 1
            else:
                stats['checked_in'] += 1
        else:
             stats['waiting'] += 1

        waiting_list.append({
            'appointment_id': str(appt['_id']),
            'name': patient_name,
            'phone': patient['personalInfo']['phone'] if patient else 'Không rõ',
            'id': patient.get('_id', '') if patient else '',
            'appointment_type': appt.get('type', 'Không rõ'),
            'check_in_time': appt.get('timeSlot'),
            'doctor': doctor_name,
            'status': appt.get('status'),
            'status_class': status_class
        })
    # print("Waiting list:", waiting_list)
    # Truy vấn danh sách bác sĩ từ MongoDB
    doctors = mongo.db.doctors.find({}, {
        '_id': 1,
        'personalInfo.fullName': 1,
        'professionalInfo.specialization': 1
    })
    stats['total_appointments'] = len(waiting_list)
    # Chuyển đổi ObjectId sang chuỗi và chuẩn bị dữ liệu
    doctors_list = [{
        '_id': str(doctor['_id']),
        'personalInfo': {
            'fullName': doctor['personalInfo']['fullName']
        },
        'professionalInfo': {
            'specialization': doctor['professionalInfo'].get('specialization', 'Không rõ')
        }
    } for doctor in doctors]   
    return render_template(
        'receptionist/dashboard.html',
        stats=stats,
        waiting_list=waiting_list,
        recent_activities=recent_activities,
        notifications_count=3,  # hoặc context processor như đã nói
        today=today,
        doctors=doctors_list,
        current_user_id=current_user_id)
