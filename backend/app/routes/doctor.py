from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from ..extensions import mongo
from bson import ObjectId
from datetime import datetime

doctor_bp = Blueprint('doctor', __name__)

@doctor_bp.route('/dashboard')
@login_required
def dashboard():
    # Get today's appointments
    today_appointments = mongo.db.appointments.find({
        'doctor_id': current_user.user_data.get('staff_id'),
        'date': {'$gte': datetime.now().replace(hour=0, minute=0, second=0),
                 '$lt': datetime.now().replace(hour=23, minute=59, second=59)}
    })

    # Get monitored patients
    monitored_patients = mongo.db.patients.find({
        'monitoring_doctor_id': current_user.user_data.get('staff_id')
    }).limit(5)

    stats = {
        'total_appointments': mongo.db.appointments.count_documents({
            'doctor_id': current_user.user_data.get('staff_id'),
            'date': {'$gte': datetime.now().replace(hour=0, minute=0, second=0),
                    '$lt': datetime.now().replace(hour=23, minute=59, second=59)}
        }),
        'completed_appointments': mongo.db.appointments.count_documents({
            'doctor_id': current_user.user_data.get('staff_id'),
            'date': {'$gte': datetime.now().replace(hour=0, minute=0, second=0),
                    '$lt': datetime.now().replace(hour=23, minute=59, second=59)},
            'status': 'completed'
        }),
        'waiting_appointments': mongo.db.appointments.count_documents({
            'doctor_id': current_user.user_data.get('staff_id'),
            'date': {'$gte': datetime.now().replace(hour=0, minute=0, second=0),
                    '$lt': datetime.now().replace(hour=23, minute=59, second=59)},
            'status': 'waiting'
        }),
        'prescriptions': mongo.db.prescriptions.count_documents({
            'doctor_id': current_user.user_data.get('staff_id'),
            'created_at': {'$gte': datetime.now().replace(hour=0, minute=0, second=0),
                          '$lt': datetime.now().replace(hour=23, minute=59, second=59)}
        })
    }

    return render_template('doctor/dashboard.html',
                         stats=stats,
                         appointments=list(today_appointments),
                         monitored_patients=list(monitored_patients))

@doctor_bp.route('/medical-records')
@login_required
def medical_records():
    return render_template('doctor/medical_records.html')

@doctor_bp.route('/prescriptions')
@login_required
def prescriptions():
    return render_template('doctor/prescriptions.html')

@doctor_bp.route('/patients')
@login_required
def patients():
    patients = mongo.db.patients.find()
    return render_template('doctor/patients.html', patients=list(patients))

@doctor_bp.route('/patient/<string:patient_id>')
@login_required
def patient_details(patient_id):
    patient = mongo.db.patients.find_one({'_id': ObjectId(patient_id)})
    if not patient:
        return "Patient not found", 404
    return render_template('doctor/patient_details.html', patient=patient)

@doctor_bp.route('/examination/<string:appointment_id>')
@login_required
def examination(appointment_id):
    appointment = mongo.db.appointments.find_one({'_id': ObjectId(appointment_id)})
    if not appointment:
        return "Appointment not found", 404
    return render_template('doctor/examination.html', appointment=appointment)

@doctor_bp.route('/profile')
@login_required
def profile():
    doctor = mongo.db.doctors.find_one({'_id': current_user.user_data.get('staff_id')})
    if not doctor:
        return "Doctor profile not found", 404
    return render_template('doctor/profile.html', doctor=doctor)

# API endpoints for AJAX requests
@doctor_bp.route('/api/today-appointments')
@login_required
def get_today_appointments():
    appointments = mongo.db.appointments.find({
        'doctor_id': current_user.user_data.get('staff_id'),
        'date': {'$gte': datetime.now().replace(hour=0, minute=0, second=0),
                '$lt': datetime.now().replace(hour=23, minute=59, second=59)}
    })
    return jsonify(list(appointments))