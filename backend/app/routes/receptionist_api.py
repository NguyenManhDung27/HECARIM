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
from datetime import datetime, time, timedelta, timezone
import math

receptionist_api = Blueprint('receptionist/api', __name__)

@receptionist_api.route('/appointments/<appointment_id>')
@login_required
@role_required('receptionist')
@handle_api_error
def get_appointment(appointment_id):
    # ... (giữ nguyên nội dung get_appointment)
    pass

@receptionist_api.route('/appointments', methods=['POST'])
@login_required
@role_required('receptionist')
@handle_api_error
def create_appointment():
    data = request.get_json()
    appointment_data = {
        'patientId': data['patient_id'],
        'doctorId': data['doctor_id'],
        'appointmentTime': datetime.strptime(data['appointment_date'], '%Y-%m-%d'),
        'timeSlot': data['time_slot'],
        'status': 'scheduled',
        'notes': data.get('notes', ''),
        'reason': data.get('reason', ''),
        'createdAt': datetime.now(),
        'updatedAt': datetime.now()
    }
    try:
        mongo.db.appointments.insert_one(appointment_data)
        print("Dữ liệu đã được lưu thành công!")
    except Exception as e:
        print(f"Lỗi khi lưu dữ liệu: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    print("Received JSON:", data)
    return jsonify({'success': True, "message": "Appointment created successfully"}), 200

@receptionist_api.route('/patients/search', methods=['GET'])
@login_required
@role_required('receptionist')
def search_patients():
    print("Hàm search_patients đã được gọi!")
    query = request.args.get('q', '').strip()
    
    # Kiểm tra nếu query quá ngắn
    if len(query) < 2:
        return jsonify({'message': 'Query quá ngắn', 'patients': []}), 400

    # Tìm kiếm theo idNumber hoặc fullName
    patients = mongo.db.patients.find({
        '$or': [
            {'personalInfo.idNumber': {'$regex': query, '$options': 'i'}},
            {'personalInfo.fullName': {'$regex': query, '$options': 'i'}}
        ]
    }).limit(10)

    # Xử lý kết quả
    results = [{
        'id': str(patient['_id']),
        'idNumber': patient['personalInfo'].get('idNumber', 'Không rõ'),
        'fullName': patient['personalInfo'].get('fullName', 'Không rõ'),
        'phone': patient['personalInfo'].get('phone', 'Không rõ'),
        'address': patient['personalInfo'].get('address', 'Không rõ')
    } for patient in patients]

    # Trả về kết quả
    if not results:
        return jsonify({'message': 'Không tìm thấy bệnh nhân', 'patients': []}), 404

    return jsonify({'patients': results}), 200

@receptionist_api.route('/doctors', methods=['GET'])
@login_required
@role_required('receptionist')
def search_doctors():
    department_name = request.args.get('department', '').strip()
    if not department_name:
        return jsonify([])
    try:
        doctors = mongo.db.doctors.find(
            {'professionalInfo.department': {'$regex': department_name, '$options': 'i'}},
            {
                '_id': 1,
                'personalInfo.fullName': 1,
                'professionalInfo.specialization': 1,
                'personalInfo.phone': 1
            }
        )
        results = [{
            'id': str(doctor['_id']),
            'name': doctor['personalInfo']['fullName'],
            'specialization': doctor['professionalInfo'].get('specialization', 'Không rõ'),
            'phone': doctor['personalInfo'].get('phone', 'Không rõ')
        } for doctor in doctors]
        return jsonify(results)
    except Exception as e:
        print(f"Lỗi khi tìm bác sĩ: {e}")
        return jsonify({'error': 'Có lỗi xảy ra khi tìm bác sĩ'}), 500

@receptionist_api.route('/patients', methods=['POST'])
@login_required
@role_required('receptionist')
@handle_api_error
def create_patient():
    data = request.get_json()
    existing_patient = mongo.db.patients.find_one({'personalInfo.idNumber': data['personalInfo']['idNumber']})
    if existing_patient:
        print(f"Bệnh nhân với ID {data['personalInfo']['idNumber']} đã tồn tại!")
        return jsonify({'success': False, 'error': 'CCCD đã được đăng kí trước đó'}), 400
    patient = {
    'patientId': f"BN{int(datetime.now().timestamp())}",
    'personalInfo': {
        'fullName': data['personalInfo']['fullName'],
        'dateOfBirth': data['personalInfo']['dateOfBirth'],
        'gender': data['personalInfo']['gender'],
        'idNumber': data['personalInfo']['idNumber'],
        'address': data['personalInfo']['address'],
        'phone': data['personalInfo']['phone'],
        'email': data['personalInfo']['email']
    },
    'healthInfo': {
        'allergies': data['healthInfo']['allergies'],
        'chronicDiseases': data['healthInfo']['chronicDiseases'],
        'bloodType': data['healthInfo']['bloodType'],
        'height': data['healthInfo']['height'],
        'weight': data['healthInfo']['weight'],
        'familyMedicalHistory': data['healthInfo']['familyMedicalHistory']
    },
    'createdAt': datetime.now(),
    'updatedAt': datetime.now()
    }
    try:
        mongo.db.patients.insert_one(patient)
        print("Dữ liệu đã được lưu thành công!")
    except Exception as e:
        print(f"Lỗi khi lưu dữ liệu: {e}")
        return jsonify({'error': 'Internal Server Error'}), 500
    return jsonify({'success': True, 'message': 'Patient created successfully'}), 201

@receptionist_api.route('/appointments/time-slots', methods=['GET'])
@login_required
@role_required('receptionist')
@handle_api_error
def get_time_slots():
    doctor_id = request.args.get('doctorId')
    date_str = request.args.get('date')

    if not doctor_id or not date_str:
        return jsonify({'error': 'doctorId and date are required'}), 400

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    # Giới hạn thời gian làm việc: 7:00 - 18:00
    start_of_day = datetime.combine(date, time.min).replace(tzinfo=timezone.utc)
    end_of_day = datetime.combine(date, time.max).replace(tzinfo=timezone.utc)
    print("Start of day:", start_of_day.isoformat())
    print("End of day:", end_of_day.isoformat())
    # Truy vấn chỉ những lịch của bác sĩ và trong ngày cụ thể
    appointments = mongo.db.appointments.find({
        'doctorId': doctor_id,
        'appointmentTime': {
            '$gte': start_of_day,
            '$lt': end_of_day
        }
    })

    booked_times = [appt['timeSlot'] for appt in appointments]
    print("Khung giờ đã đặt:", booked_times)
    start_of_day = datetime.combine(date, time(7, 0, tzinfo=timezone.utc))
    end_of_day = datetime.combine(date, time(18, 0, tzinfo=timezone.utc))
    # Tạo danh sách khung giờ mỗi 60 phút
    time_slots = []
    current = start_of_day
    while current < end_of_day:
        time_str = current.strftime('%H:%M')
        time_slots.append({
            'time': time_str,
            'available': time_str not in booked_times
        })
        current += timedelta(minutes=60)

    return jsonify(time_slots), 200

@receptionist_api.route('/patients', methods=['GET'])
@login_required
@role_required('receptionist')
@handle_api_error
def list_patients():
    pass


# Helper

def get_department_name(department_id):
    department = mongo.db.departments.find_one({'_id': department_id})
    return department['name'] if department else 'Unknown'