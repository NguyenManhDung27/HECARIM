from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from ..extensions import mongo
from bson import ObjectId
from datetime import datetime

patient_bp = Blueprint('patient', __name__)

@patient_bp.route('/dashboard')
@login_required
def dashboard():
    # Lấy thông tin bệnh nhân
    patient = mongo.db.patients.find_one({'_id': ObjectId(current_user.user_data.get('patient_id'))})
    
    # Lấy lịch hẹn sắp tới
    upcoming_appointments = list(mongo.db.appointments.find({
        'patientId': str(current_user.user_data.get('patient_id')),
        'appointmentTime': {'$gte': datetime.now()}
    }).sort('appointmentTime', 1).limit(5))

    # Thêm thông tin bác sĩ vào lịch hẹn
    for appointment in upcoming_appointments:
        doctor = mongo.db.doctors.find_one({'_id': ObjectId(appointment['doctorId'])})
        appointment['doctor_name'] = doctor['personalInfo']['fullName'] if doctor else 'Không xác định'
        appointment['department'] = doctor['department'] if doctor else 'Không xác định'
        appointment['status_color'] = 'warning' if appointment['status'] == 'pending' else 'success'

    # Lấy lịch sử khám gần đây
    recent_records = list(mongo.db.medical_records.find({
        'patientId': str(current_user.user_data.get('patient_id'))
    }).sort('date', -1).limit(5))

    # Thêm thông tin bác sĩ vào lịch sử khám
    for record in recent_records:
        doctor = mongo.db.doctors.find_one({'_id': ObjectId(record['doctorId'])})
        record['doctor_name'] = doctor['personalInfo']['fullName'] if doctor else 'Không xác định'
        record['has_prescription'] = bool(mongo.db.prescriptions.find_one({
            'patient_id': ObjectId(current_user.user_data.get('patient_id')),
            'medical_record_id': record['_id']
        }))

    return render_template(
        'patient/dashboard.html',
        patient=patient,
        upcoming_appointments=upcoming_appointments,
        recent_records=recent_records,
        notifications_count=3
    )

@patient_bp.route('/appointments')
@login_required
def appointments():
    # Lấy danh sách khoa
    departments = list(mongo.db.departments.find())
    
    # Lấy tất cả lịch hẹn của bệnh nhân
    appointments = list(mongo.db.appointments.find({
        'patientId': str(current_user.user_data.get('patient_id'))
    }).sort('appointmentTime', -1))

    # Thêm thông tin chi tiết cho mỗi lịch hẹn
    for appointment in appointments:
        doctor = mongo.db.doctors.find_one({'_id': ObjectId(appointment['doctorId'])})
        appointment['doctor_name'] = doctor['personalInfo']['fullName'] if doctor else 'Không xác định'
        appointment['department'] = doctor['department'] if doctor else 'Không xác định'
        appointment['status_color'] = {
            'pending': 'warning',
            'confirmed': 'primary',
            'completed': 'success',
            'cancelled': 'danger'
        }.get(appointment['status'], 'secondary')
        
        # Kiểm tra xem có thể hủy hoặc đổi lịch không
        appointment['can_cancel'] = appointment['status'] in ['pending', 'confirmed']
        appointment['can_reschedule'] = appointment['status'] in ['pending', 'confirmed']

    return render_template(
        'patient/appointments.html',
        departments=departments,
        appointments=appointments,
        notifications_count=3
    )

@patient_bp.route('/records')
@login_required
def records():
    # Lấy toàn bộ lịch sử khám bệnh
    medical_records = list(mongo.db.medical_records.find({
        'patientId': str(current_user.user_data.get('patient_id'))
    }).sort('date', -1))

    # Thêm thông tin chi tiết cho mỗi bản ghi
    for record in medical_records:
        # Thông tin bác sĩ
        doctor = mongo.db.doctors.find_one({'_id': ObjectId(record['doctorId'])})
        record['doctor_name'] = doctor['personalInfo']['fullName'] if doctor else 'Không xác định'
        record['department'] = doctor['department'] if doctor else 'Không xác định'
        
        # Thông tin đơn thuốc
        prescription = mongo.db.prescriptions.find_one({
            'medical_record_id': record['_id']
        })
        if prescription:
            record['has_prescription'] = True
            record['prescription'] = prescription['medications']
        else:
            record['has_prescription'] = False
            record['prescription'] = []

    # Lấy tổng quan sức khỏe
    medical_summary = mongo.db.medical_summaries.find_one({
        'patientId': str(current_user.user_data.get('patient_id'))
    })

    # Lấy chỉ số sức khỏe gần đây nhất
    health_metrics = mongo.db.health_metrics.find_one({
        'patientId': str(current_user.user_data.get('patient_id'))
    }, sort=[('date', -1)])

    return render_template(
        'patient/records.html',
        medical_records=medical_records,
        medical_summary=medical_summary,
        health_metrics=health_metrics,
        notifications_count=3
    )

@patient_bp.route('/prescriptions')
@login_required
def prescriptions():
    # Lấy đơn thuốc đang sử dụng
    active_prescriptions = list(mongo.db.prescriptions.find({
        'patient_id': ObjectId(current_user.user_data.get('patient_id')),
        'status': 'active'
    }).sort('issue_date', -1))

    # Lấy lịch sử đơn thuốc
    prescription_history = list(mongo.db.prescriptions.find({
        'patient_id': ObjectId(current_user.user_data.get('patient_id')),
        'status': {'$ne': 'active'}
    }).sort('issue_date', -1))

    # Thêm thông tin chi tiết cho mỗi đơn thuốc
    for prescription in active_prescriptions + prescription_history:
        doctor = mongo.db.doctors.find_one({'_id': ObjectId(prescription['doctor_id'])})
        prescription['doctor_name'] = doctor['personalInfo']['fullName'] if doctor else 'Không xác định'
        prescription['status_color'] = {
            'active': 'success',
            'completed': 'primary',
            'cancelled': 'danger'
        }.get(prescription['status'], 'secondary')

    return render_template(
        'patient/prescriptions.html',
        active_prescriptions=active_prescriptions,
        prescription_history=prescription_history,
        notifications_count=3
    )

@patient_bp.route('/profile')
@login_required
def profile():
    patient = mongo.db.patients.find_one({'_id': ObjectId(current_user.user_data.get('patient_id'))})
    if not patient:
        return "Patient profile not found", 404
    return render_template('auth/profile.html', patient=patient, notifications_count=3)