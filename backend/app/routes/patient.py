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
    
    patient = mongo.db.patients.find_one({'_id': ObjectId(current_user.user_data['patient_id'])})

    
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
    departments = list(mongo.db.doctors.distinct('professionalInfo.department'))
    # Lấy tất cả lịch hẹn của bệnh nhân
    appointments = list(mongo.db.appointments.find({
        'patientId': str(current_user.user_data.get('patient_id'))
    }).sort('appointmentTime', -1))

    # Thêm thông tin chi tiết cho mỗi lịch hẹn
    for appointment in appointments:
        doctor = mongo.db.doctors.find_one({'_id': ObjectId(appointment['doctorId'])})
        appointment['doctor_name'] = doctor['personalInfo']['fullName'] if doctor else 'Không xác định'
        appointment['department'] = doctor['professionalInfo']['department'] if doctor else 'Không xác định'
        appointment['status_color'] = {
            'pending': 'warning',
            'confirmed': 'primary',
            'completed': 'success',
            'cancelled': 'danger'
        }.get(appointment['status'], 'secondary')
        
        # Kiểm tra xem có thể hủy hoặc đổi lịch không
        appointment['can_cancel'] = appointment['status'] in ['pending', 'confirmed']
        appointment['can_reschedule'] = appointment['status'] in ['pending', 'confirmed']
        print("Dữ liệu departments:", departments)
    return render_template(
        'patient/appointments.html',
        departments =departments,
        appointments=appointments,
        notifications_count=3
    )

@patient_bp.route('/records', methods=['GET'])
@login_required
def records():
    try:
        user = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
        patient_id = str(user['patient_id']) if user else None

        # Fetch only the records belonging to the current user
        medical_records = list(mongo.db.medical_records.find({'patientId': ObjectId(patient_id)}))
        patients = list(mongo.db.patients.find())
        for patient in patients:
            patient['_id'] = str(patient['_id'])
        patient_map = {str(patient['_id']): patient['personalInfo']['fullName'] for patient in patients}

        for record in medical_records:
            # Convert ObjectId to string
            record['_id'] = str(record['_id'])
            record['patientId'] = str(record.get('patientId', ''))
            record['doctorId'] = str(record.get('doctorId', ''))
            record['notes'] = record.get('notes', '')
            # Format dates
            record['visitDate'] = record['visitDate'].strftime('%Y-%m-%d') if record.get('visitDate') else None
            record['patient_name'] = patient_map.get(record['patientId'], 'Không xác định')
            record['symptoms'] = record.get('symptoms', '')
            record['diagnosis'] = record.get('diagnosis', '')

        if isinstance(record['followUp'].get('recommendedDate'), datetime):
            record['followUp']['recommendedDate'] = record['followUp']['recommendedDate'].strftime('%Y-%m-%d')
        elif isinstance(record['followUp'].get('recommendedDate'), str):
            record['followUp']['recommendedDate'] = record['followUp']['recommendedDate']  # Keep it as is
        else:
            record['followUp']['recommendedDate'] = None  # Handle case where it's null

        return render_template(
            'patient/records.html',
            medical_records=medical_records,
            notifications_count=3
        )
    except Exception as e:
        print(f"Error fetching medical records: {e}")
        return render_template('patient/records.html', medical_records=[],notifications_count=3)

@patient_bp.route('/prescriptions')
@login_required
def prescriptions():
    # Lấy đơn thuốc đang sử dụng
    active_prescriptions = list(mongo.db.prescriptions.find({
        'patient_id': ObjectId(current_user.user_data.get('patient_id')),
        'status': 'active'
    }).sort('issue_date', -1))

    # Thêm thông tin chi tiết cho mỗi đơn thuốc
    for prescription in active_prescriptions:
        user = mongo.db.users.find_one({'_id': ObjectId(prescription['doctor_id'])})
         # Lấy doctor_id từ user
        doctor_id = user['staff_id'] if user else None
        # Truy vấn doctor từ collection doctors
        doctor = mongo.db.doctors.find_one({'_id': ObjectId(doctor_id)}) if doctor_id else None
        prescription['doctor_name'] = doctor['personalInfo']['fullName'] if doctor else 'Không xác định'
        prescription['dosage'] = prescription['medications'][0]['dosage'] if prescription['medications'] else 'Không xác định'
        prescription['frequency'] = prescription['medications'][0]['frequency'] if prescription['medications'] else 'Không xác định'
        prescription['duration'] = prescription['medications'][0]['duration'] if prescription['medications'] else 'Không xác định'
        prescription['prescribed_date'] = prescription['issue_date'].strftime('%Y-%m-%d') if isinstance(prescription['issue_date'], datetime) else prescription['issue_date']
        
        
        if prescription.get("medications"):  # Ensures the list exists and is not empty
            med_id = prescription["medications"][0].get("id")  # Retrieve medication ID safely
            medic_name = mongo.db.medications.find_one({'_id': ObjectId(med_id)}) if med_id else None
        else:
            medic_name = None  # No medication found
        prescription['medicine_name'] = medic_name['genericName'] if medic_name else 'Không xác định'

    return render_template(
        'patient/prescriptions.html',
        active_prescriptions=active_prescriptions,
        notifications_count=3
    )

@patient_bp.route('/profile')
@login_required
def profile():
    patient_id = current_user.users.get('patient_id')
    
    # Ensure patient_id is an ObjectId
    if not isinstance(patient_id, ObjectId):
        patient_id = ObjectId(patient_id)
    
    patient = mongo.db.patients.find_one({'_id': patient_id})
    if not patient:
        return "Patient profile not found", 404
    
    return render_template('auth/profile.html', patient=patient, notifications_count=3)

@patient_bp.route('/invoices')
@login_required
def invoices():
    return render_template('patient/invoices.html', notifications_count=3)