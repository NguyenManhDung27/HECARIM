from flask import Blueprint, render_template
from flask_login import login_required, current_user
from backend.app.utils.auth_utils import role_required
from backend.app import mongo
from bson import ObjectId

patient_bp = Blueprint('patient', __name__)

@patient_bp.route('/dashboard')
@login_required
@role_required('patient')
def dashboard():
    # Get patient's upcoming appointments
    upcoming_appointments = list(mongo.db.appointments.find({
        'patientId': ObjectId(current_user.user_data.get('patient_id')),
        'status': {'$in': ['scheduled', 'confirmed']}
    }).sort('timeSlot.start', 1))

    # Get patient's current prescriptions
    current_prescriptions = list(mongo.db.prescriptions.find({
        'patientId': ObjectId(current_user.user_data.get('patient_id')),
        'status': 'active'
    }))

    # Get patient's health info
    patient = mongo.db.patients.find_one({
        '_id': ObjectId(current_user.user_data.get('patient_id'))
    })

    # Format the data for template
    formatted_appointments = [{
        'date': appt['timeSlot']['start'].strftime('%d/%m/%Y'),
        'time': appt['timeSlot']['start'].strftime('%H:%M'),
        'doctor_name': get_doctor_name(appt['doctorId']),
        'department': get_department_name(appt['doctorId']),
        'status': format_appointment_status(appt['status']),
        'status_class': get_status_class(appt['status'])
    } for appt in upcoming_appointments]

    formatted_prescriptions = [{
        'date': presc['issueDate'].strftime('%d/%m/%Y'),
        'medication_name': get_medication_name(presc['medications'][0]['medicationId']),
        'dosage': presc['medications'][0]['dosage'],
        'instructions': presc['medications'][0]['instructions'],
        'status': format_prescription_status(presc['status']),
        'status_class': get_status_class(presc['status'])
    } for presc in current_prescriptions]

    health_info = {
        'height': patient['healthInfo'].get('height', 'N/A'),
        'weight': patient['healthInfo'].get('weight', 'N/A'),
        'blood_type': patient['healthInfo'].get('bloodType', 'N/A'),
        'allergies': patient['healthInfo'].get('allergies', [])
    }

    return render_template('patient/dashboard.html',
                         upcoming_appointments=formatted_appointments,
                         current_prescriptions=formatted_prescriptions,
                         health_info=health_info)

def get_doctor_name(doctor_id):
    doctor = mongo.db.doctors.find_one({'_id': doctor_id})
    return doctor['personalInfo']['fullName'] if doctor else 'N/A'

def get_department_name(doctor_id):
    doctor = mongo.db.doctors.find_one({'_id': doctor_id})
    return doctor['professionalInfo']['department'] if doctor else 'N/A'

def get_medication_name(medication_id):
    medication = mongo.db.medications.find_one({'_id': medication_id})
    return medication['name'] if medication else 'N/A'

def format_appointment_status(status):
    status_map = {
        'scheduled': 'Đã đặt lịch',
        'confirmed': 'Đã xác nhận',
        'completed': 'Đã hoàn thành',
        'cancelled': 'Đã hủy',
        'missed': 'Vắng mặt'
    }
    return status_map.get(status, status)

def format_prescription_status(status):
    status_map = {
        'active': 'Đang sử dụng',
        'completed': 'Đã hoàn thành',
        'cancelled': 'Đã hủy'
    }
    return status_map.get(status, status)

def get_status_class(status):
    status_class_map = {
        'scheduled': 'warning',
        'confirmed': 'success',
        'completed': 'success',
        'cancelled': 'error',
        'missed': 'error',
        'active': 'success'
    }
    return status_class_map.get(status, 'warning')