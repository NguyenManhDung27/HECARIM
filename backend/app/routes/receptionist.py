from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from backend.app.utils.auth_utils import role_required
from backend.app import mongo
from bson import ObjectId
from datetime import datetime, timedelta

receptionist_bp = Blueprint('receptionist', __name__)

@receptionist_bp.route('/dashboard')
@login_required
@role_required('receptionist')
def dashboard():
    # Get today's appointments
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    
    todays_appointments = list(mongo.db.appointments.find({
        'timeSlot.start': {
            '$gte': today,
            '$lt': tomorrow
        }
    }).sort('timeSlot.start', 1))

    # Get pending invoices
    pending_invoices = list(mongo.db.invoices.find({
        'status': 'pending'
    }).sort('issueDate', 1))

    # Get daily statistics
    daily_stats = {
        'total_appointments': len(todays_appointments),
        'checked_in': len([a for a in todays_appointments if a['status'] == 'in_progress']),
        'new_patients': mongo.db.patients.count_documents({
            'createdAt': {
                '$gte': today,
                '$lt': tomorrow
            }
        }),
        'processed_invoices': mongo.db.invoices.count_documents({
            'status': 'paid',
            'paymentDate': {
                '$gte': today,
                '$lt': tomorrow
            }
        })
    }

    # Format appointments for template
    formatted_appointments = [{
        'time': appt['timeSlot']['start'].strftime('%H:%M'),
        'patient_id': get_patient_id(appt['patientId']),
        'patient_name': get_patient_name(appt['patientId']),
        'doctor_name': get_doctor_name(appt['doctorId']),
        'type': format_appointment_type(appt['type']),
        'status': format_appointment_status(appt['status']),
        'status_class': get_status_class(appt['status']),
        'id': str(appt['_id'])
    } for appt in todays_appointments]

    # Format invoices for template
    formatted_invoices = [{
        'id': str(inv['_id']),
        'patient_id': get_patient_id(inv['patientId']),
        'patient_name': get_patient_name(inv['patientId']),
        'total_amount': format_currency(inv['grandTotal'])
    } for inv in pending_invoices]

    return render_template('receptionist/dashboard.html',
                         todays_appointments=formatted_appointments,
                         pending_invoices=formatted_invoices,
                         daily_stats=daily_stats)

@receptionist_bp.route('/appointments/new')
@login_required
@role_required('receptionist')
def new_appointment():
    print("Loading departments...")
    departments = mongo.db.doctors.distinct('professionalInfo.department')
    # Render file appointments.html và truyền dữ liệu vào
    return render_template('receptionist/appointment_form.html', departments=departments)

@receptionist_bp.route('/appointments/<appointment_id>/status', methods=['POST'])
@login_required
@role_required('receptionist')
def update_appointment_status(appointment_id):
    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({'error': 'Status is required'}), 400

    try:
        result = mongo.db.appointments.update_one(
            {'_id': ObjectId(appointment_id)},
            {'$set': {
                'status': new_status,
                'updatedAt': datetime.now()
            }}
        )
        
        if result.modified_count:
            return jsonify({'message': 'Status updated successfully'})
        return jsonify({'error': 'Appointment not found'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_patient_id(patient_id):
    patient = mongo.db.patients.find_one({'_id': patient_id})
    return patient['patientId'] if patient else 'N/A'

def get_patient_name(patient_id):
    patient = mongo.db.patients.find_one({'_id': patient_id})
    return patient['personalInfo']['fullName'] if patient else 'N/A'

def get_doctor_name(doctor_id):
    doctor = mongo.db.doctors.find_one({'_id': doctor_id})
    return doctor['personalInfo']['fullName'] if doctor else 'N/A'

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
        'checked_in': 'Đã tiếp nhận',
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
        'checked_in': 'success',
        'in_progress': 'warning',
        'completed': 'success',
        'cancelled': 'error',
        'missed': 'error'
    }
    return status_class_map.get(status, 'warning')

def format_currency(amount):
    """Format amount in VND"""
    return f"{amount:,.0f} ₫"


@receptionist_bp.route('/appointments')
@login_required
@role_required('receptionist')
def appointment_dashboard():
    # Lấy danh sách lịch hẹn từ MongoDB
    appointments = list(mongo.db.appointments.find().sort('timeSlot.start', 1))

    # Định dạng dữ liệu lịch hẹn để hiển thị trên giao diện
    formatted_appointments = [{
        'id': str(appt['_id']),
        'time': appt['timeSlot']['start'].strftime('%H:%M %d/%m/%Y'),
        'patient_name': get_patient_name(appt['patientId']),
        'doctor_name': get_doctor_name(appt['doctorId']),
        'type': format_appointment_type(appt['type']),
        'status': format_appointment_status(appt['status']),
        'status_class': get_status_class(appt['status'])
    } for appt in appointments]
    departments = mongo.db.doctors.distinct('professionalInfo.department')
    print(departments)
    # Render file appointments.html và truyền dữ liệu vào
    return render_template('receptionist/appointments.html', appointments=formatted_appointments, departments=departments)

# @receptionist_bp.route('/appointments/new')
# @login_required
# @role_required('receptionist')
# def load_departments():
#     print("Loading departments...")
#     departments = mongo.db.doctors.distinct('professionalInfo.department')
#     print(departments)
#     # Render file appointments.html và truyền dữ liệu vào
#     return render_template('receptionist/appointments.html', departments=departments)
