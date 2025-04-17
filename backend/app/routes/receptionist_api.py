from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from backend.app.utils.auth_utils import role_required
from backend.app.utils.api_utils import (
    handle_api_error, 
    validate_appointment_data,
    format_appointment_response,
    format_doctor_response,
    format_patient_response,
    api_error
)
from backend.app import mongo
from bson import ObjectId
from datetime import datetime, timedelta
import math

receptionist_api = Blueprint('receptionist_api', __name__)

@receptionist_api.route('/appointments')
@login_required
@role_required('receptionist')
@handle_api_error
def list_appointments():
    # Get query parameters
    date_str = request.args.get('date')
    department = request.args.get('department')
    status = request.args.get('status')
    search = request.args.get('search', '').strip()
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 10))

    # Build query
    query = {}
    
    # Date filter
    if date_str:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            next_day = date + timedelta(days=1)
            query['timeSlot.start'] = {
                '$gte': date,
                '$lt': next_day
            }
        except ValueError:
            return api_error('Invalid date format', 400)
    
    # Department filter
    if department:
        try:
            doctor_ids = [d['_id'] for d in mongo.db.doctors.find(
                {'professionalInfo.department': ObjectId(department)},
                {'_id': 1}
            )]
            if doctor_ids:
                query['doctorId'] = {'$in': doctor_ids}
        except Exception:
            return api_error('Invalid department ID', 400)
    
    # Status filter
    if status:
        query['status'] = status
    
    # Search
    if search:
        # Get matching patient IDs
        patient_ids = [p['_id'] for p in mongo.db.patients.find({
            '$or': [
                {'patientId': {'$regex': search, '$options': 'i'}},
                {'personalInfo.fullName': {'$regex': search, '$options': 'i'}}
            ]
        }, {'_id': 1})]
        
        # Get matching doctor IDs
        doctor_ids = [d['_id'] for d in mongo.db.doctors.find({
            'personalInfo.fullName': {'$regex': search, '$options': 'i'}
        }, {'_id': 1})]
        
        if patient_ids or doctor_ids:
            query['$or'] = []
            if patient_ids:
                query['$or'].append({'patientId': {'$in': patient_ids}})
            if doctor_ids:
                query['$or'].append({'doctorId': {'$in': doctor_ids}})
        else:
            # No matches found
            return jsonify({
                'appointments': [],
                'total_pages': 0,
                'current_page': page,
                'total_items': 0
            })
    
    # Calculate pagination
    total = mongo.db.appointments.count_documents(query)
    total_pages = math.ceil(total / page_size)
    skip = (page - 1) * page_size
    
    # Get appointments
    appointments = list(mongo.db.appointments.find(query)
                       .sort('timeSlot.start', -1)
                       .skip(skip)
                       .limit(page_size))
    
    # Format appointments
    formatted_appointments = []
    for appt in appointments:
        # Get patient info
        patient = mongo.db.patients.find_one({'_id': appt['patientId']})
        
        # Get doctor info
        doctor = mongo.db.doctors.find_one({'_id': appt['doctorId']})
        
        if patient and doctor:
            formatted_appt = {
                'id': str(appt['_id']),
                'patientId': patient.get('patientId', 'Unknown'),
                'patientName': patient['personalInfo']['fullName'],
                'doctorName': doctor['personalInfo']['fullName'],
                'department': get_department_name(doctor['professionalInfo']['department']),
                'timeSlot': {
                    'start': appt['timeSlot']['start'].isoformat(),
                    'end': appt['timeSlot']['end'].isoformat()
                },
                'type': appt['type'],
                'status': appt['status'],
                'reason': appt.get('reason', ''),
                'notes': appt.get('notes', '')
            }
            formatted_appointments.append(formatted_appt)
    
    return jsonify({
        'appointments': formatted_appointments,
        'total_pages': total_pages,
        'current_page': page,
        'total_items': total
    })

@receptionist_api.route('/appointments/<appointment_id>')
@login_required
@role_required('receptionist')
@handle_api_error
def get_appointment(appointment_id):
    appointment = mongo.db.appointments.find_one({'_id': ObjectId(appointment_id)})
    if not appointment:
        return api_error('Appointment not found', 404)
    
    # Get related data
    patient = mongo.db.patients.find_one({'_id': appointment['patientId']})
    doctor = mongo.db.doctors.find_one({'_id': appointment['doctorId']})
    
    if not patient or not doctor:
        return api_error('Invalid appointment data', 500)
    
    # Format response
    response = {
        'id': str(appointment['_id']),
        'patientId': patient.get('patientId', 'Unknown'),
        'patientName': patient['personalInfo']['fullName'],
        'doctorName': doctor['personalInfo']['fullName'],
        'department': get_department_name(doctor['professionalInfo']['department']),
        'timeSlot': {
            'start': appointment['timeSlot']['start'].isoformat(),
            'end': appointment['timeSlot']['end'].isoformat()
        },
        'type': appointment['type'],
        'status': appointment['status'],
        'reason': appointment.get('reason', ''),
        'notes': appointment.get('notes', ''),
        'createdAt': appointment['createdAt'].isoformat(),
        'updatedAt': appointment['updatedAt'].isoformat()
    }
    
    return jsonify(response)

@receptionist_api.route('/appointments/<appointment_id>/status', methods=['POST'])
@login_required
@role_required('receptionist')
@handle_api_error
def update_appointment_status(appointment_id):
    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status:
        return api_error('Status is required', 400)
    
    valid_statuses = ['scheduled', 'confirmed', 'checked_in', 'cancelled', 'missed']
    if new_status not in valid_statuses:
        return api_error('Invalid status', 400)
    
    appointment = mongo.db.appointments.find_one({'_id': ObjectId(appointment_id)})
    if not appointment:
        return api_error('Appointment not found', 404)
    
    # Validate status transition
    current_status = appointment['status']
    if current_status == 'completed':
        return api_error('Cannot update completed appointment', 400)
    if current_status == 'cancelled' and new_status != 'scheduled':
        return api_error('Cancelled appointment can only be rescheduled', 400)
    
    # Update appointment
    result = mongo.db.appointments.update_one(
        {'_id': ObjectId(appointment_id)},
        {'$set': {
            'status': new_status,
            'updatedAt': datetime.now()
        }}
    )
    
    if result.modified_count == 0:
        return api_error('Failed to update appointment', 500)
    
    return jsonify({'message': 'Appointment status updated successfully'})

# Helper functions
def get_department_name(department_id):
    department = mongo.db.departments.find_one({'_id': department_id})
    return department['name'] if department else 'Unknown'