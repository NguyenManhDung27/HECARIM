from flask import Blueprint, render_template
from flask_login import login_required, current_user
from backend.app.utils.auth_utils import role_required
from backend.app import mongo
from bson import ObjectId
from datetime import datetime, timedelta

doctor_bp = Blueprint('doctor', __name__)

@doctor_bp.route('/dashboard')
@login_required
@role_required('doctor')
def dashboard():
    # Get today's appointments
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    todays_appointments = list(mongo.db.appointments.find({
        'doctorId': ObjectId(current_user.user_data.get('staff_id')),
        'timeSlot.start': {
            '$gte': today,
            '$lt': tomorrow
        }
    }).sort('timeSlot.start', 1))

    # Get patients that need monitoring (patients with follow-ups)
    monitored_patients = list(mongo.db.medical_reports.aggregate([
        {
            '$match': {
                'doctorId': ObjectId(current_user.user_data.get('staff_id')),
                'followUp.required': True,
                'followUp.recommendedDate': {'$gte': today}
            }
        },
        {
            '$lookup': {
                'from': 'patients',
                'localField': 'patientId',
                'foreignField': '_id',
                'as': 'patient'
            }
        },
        {'$unwind': '$patient'},
        {'$sort': {'followUp.recommendedDate': 1}},
        {'$limit': 10}
    ]))

    # Get monthly statistics
    month_start = today.replace(day=1)
    next_month = (month_start + timedelta(days=32)).replace(day=1)
    
    monthly_appointments = list(mongo.db.appointments.find({
        'doctorId': ObjectId(current_user.user_data.get('staff_id')),
        'timeSlot.start': {
            '$gte': month_start,
            '$lt': next_month
        }
    }))

    monthly_prescriptions = list(mongo.db.prescriptions.find({
        'doctorId': ObjectId(current_user.user_data.get('staff_id')),
        'issueDate': {
            '$gte': month_start,
            '$lt': next_month
        }
    }))

    # Format appointments for template
    formatted_appointments = [{
        'time': appt['timeSlot']['start'].strftime('%H:%M'),
        'patient_id': get_patient_id(appt['patientId']),
        'patient_name': get_patient_name(appt['patientId']),
        'type': format_appointment_type(appt['type']),
        'status': format_appointment_status(appt['status']),
        'status_class': get_status_class(appt['status']),
        'id': str(appt['_id'])
    } for appt in todays_appointments]

    # Format monitored patients for template
    formatted_patients = [{
        'id': get_patient_id(report['patientId']),
        'name': report['patient']['personalInfo']['fullName'],
        'diagnosis': report['diagnosis'][0] if report['diagnosis'] else 'N/A',
        'last_visit': report['visitDate'].strftime('%d/%m/%Y')
    } for report in monitored_patients]

    # Calculate statistics
    working_days = len(set(appt['timeSlot']['start'].date() for appt in monthly_appointments))
    working_days = working_days if working_days > 0 else 1

    monthly_stats = {
        'total_patients': len(monthly_appointments),
        'follow_ups': len([a for a in monthly_appointments if a['type'] == 'follow_up']),
        'prescriptions': len(monthly_prescriptions),
        'avg_patients_per_day': round(len(monthly_appointments) / working_days, 1)
    }

    return render_template('doctor/dashboard.html',
                         todays_appointments=formatted_appointments,
                         monitored_patients=formatted_patients,
                         monthly_stats=monthly_stats)

def get_patient_id(patient_id):
    patient = mongo.db.patients.find_one({'_id': patient_id})
    return patient['patientId'] if patient else 'N/A'

def get_patient_name(patient_id):
    patient = mongo.db.patients.find_one({'_id': patient_id})
    return patient['personalInfo']['fullName'] if patient else 'N/A'

def format_appointment_type(type_):
    type_map = {
        'regular': 'Khám thường',
        'follow_up': 'Tái khám',
        'emergency': 'Cấp cứu'
    }
    return type_map.get(type_, type_)

def format_appointment_status(status):
    status_map = {
        'scheduled': 'Đã đặt lịch',
        'confirmed': 'Đã xác nhận',
        'in_progress': 'Đang khám',
        'completed': 'Đã hoàn thành',
        'cancelled': 'Đã hủy',
        'missed': 'Vắng mặt'
    }
    return status_map.get(status, status)

def get_status_class(status):
    status_class_map = {
        'scheduled': 'warning',
        'confirmed': 'success',
        'in_progress': 'warning',
        'completed': 'success',
        'cancelled': 'error',
        'missed': 'error'
    }
    return status_class_map.get(status, 'warning')