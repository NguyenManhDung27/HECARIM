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

receptionist_api = Blueprint('receptionist/api', __name__)

@receptionist_api.route('/appointments')
@login_required
@role_required('receptionist')
@handle_api_error
def list_appointments():
    # ... (giữ nguyên nội dung list_appointments)
    pass

@receptionist_api.route('/appointments/<appointment_id>')
@login_required
@role_required('receptionist')
@handle_api_error
def get_appointment(appointment_id):
    # ... (giữ nguyên nội dung get_appointment)
    pass

@receptionist_api.route('/appointments/<appointment_id>/status', methods=['POST'])
@login_required
@role_required('receptionist')
@handle_api_error
def update_appointment_status(appointment_id):
    # ... (giữ nguyên nội dung update_appointment_status)
    pass

@receptionist_api.route('/search-patients', methods=['GET'])
@login_required
@role_required('receptionist')
def search_patients():
    print("Hàm search_patients đã được gọi!")
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    patients = mongo.db.patients.find({
        '$or': [
            {'name': {'$regex': query, '$options': 'i'}},
            {'patientId': {'$regex': query, '$options': 'i'}}
        ]
    }).limit(10)
    results = [{
        'id': str(patient['_id']),
        'patientId': patient.get('patientId', ''),
        'name': patient['personalInfo'].get('fullName', 'Không rõ'),
        'phone': patient['personalInfo'].get('phone', 'Không rõ')
    } for patient in patients]
    if not results:
        return jsonify({'message': 'Không tìm thấy bệnh nhân', 'patients': []})
    return jsonify(results)

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
    # print("Dữ liệu nhận được:", data)
    # required_fields = ['fullName', 'dateOfBirth', 'gender', 'phone', 'address']
    # for field in required_fields:
        # if not data.get(field):
            # print(f"Thiếu trường: {field}")
            # return api_error(f'{field} is required', 400)
    # Kiểm tra xem bệnh nhân đã tồn tại chưa    
    # print("Thông tin bệnh nhân:", data['fullName'], data['dateOfBirth'], data['gender'], data['phone'], data['address'])
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