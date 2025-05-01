from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from ..extensions import mongo
from bson import ObjectId
from datetime import datetime

doctor_api = Blueprint('doctor/api', __name__)

@doctor_api.route('/prescriptions', methods=['POST'])
@login_required
def save_prescription():
    # Parse JSON data from the request body
    data = request.get_json()
    # if not data:
    #   return jsonify({"success": False, "message": "No JSON data received or invalid JSON format"}), 400

    # Chuyển đổi medications từ các trường riêng lẻ thành danh sách
    medications = []
    if 'medications[][id]' in data:
        medications.append({
            'id': data['medications[][id]'],
            'dosage': data['medications[][dosage]'],
            'frequency': data['medications[][frequency]'],
            'duration': data['medications[][duration]'],
            'instructions': data['medications[][instructions]']
        })

    # Kiểm tra dữ liệu đầu vào
    if not data.get('patient_id') or not medications:
        return jsonify({'success': False, 'message': 'Thiếu thông tin bệnh nhân hoặc danh sách thuốc'}), 400
    # Ensure `data` is not None
    # # Tạo đơn thuốc
    prescription = {
        'patient_id': ObjectId(data['patient_id']),
        'doctor_id': ObjectId(current_user.id),  # ID của bác sĩ hiện tại
        'issue_date': datetime.strptime(data['issue_date'], '%Y-%m-%d'),  # Ngày kê đơn
        'medications': medications,  # Danh sách thuốc
        'notes': data.get('notes', ''),  # Ghi chú (nếu có)
        'status': 'pending',  # Trạng thái mặc định là "pending"
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }

    try:
        # Lưu đơn thuốc vào MongoDB
        mongo.db.prescriptions.insert_one(prescription)
        return jsonify({'success': True, 'message': 'Đơn thuốc đã được lưu thành công'}), 201
    except Exception as e:
        print(f"Lỗi khi lưu đơn thuốc: {e}")
        return jsonify({'success': False, 'message': 'Có lỗi xảy ra khi lưu đơn thuốc'}), 500
    

@doctor_api.route('/appointments/today', methods=['GET'])
@login_required
def get_today_appointments():
    today = datetime.today()
    start_of_day = datetime.combine(today.date(), datetime.min.time())
    end_of_day = datetime.combine(today.date(), datetime.max.time())
    appointments_list = mongo.db.appointments.find({
        'doctorId': str(current_user.user_data.get('staff_id')), # Thay thế bằng ID bác sĩ thực tế
        'appointmentTime': {'$gte': start_of_day, '$lte': end_of_day},
    })
    appointments=[]
    for appt in appointments_list:
        # Lấy thông tin bệnh nhân
        patient = mongo.db.patients.find_one({'_id': ObjectId(appt['patientId'])})
        # An toàn khi truy xuất thông tin
        patient_name = patient['personalInfo']['fullName'] if patient else 'Không rõ'
        appointments.append({
            '_id': str(appt['_id']),
            'patient_name': patient_name,
            'patient_id': patient.get('patientId', '') if patient else '',
            'time': appt.get('timeSlot'),
            'status': 'chờ khám',  # Hoặc trạng thái khác
            'type': appt.get('type'),  # Hoặc trạng thái khác
            'status_class': 'warning'  # hoặc tạo rule cho status_class theo trạng thái
        })  
    return jsonify(list(appointments))


@doctor_api.route('/patients/<patientId>', methods=['GET'])
@login_required
def find_patient(patientId):
    patient = mongo.db.patients.find_one({'_id': ObjectId(patientId)})
    print("Patient loaded:", patient)
    if not patient:
        return jsonify({'Không tìm thấy bệnh nhân'}), 404
    else:
        patient['_id'] = str(patient['_id'])  # Chuyển đổi ObjectId thành chuỗi
    return jsonify(patient)

@doctor_api.route('/examinations/form/<patient_id>', methods=['GET'])
@login_required
def examination_form(patient_id):
    patient = mongo.db.patients.find_one({'_id': ObjectId(patient_id)})
    if not patient:
        return "Patient not found", 404
    return render_template('doctor/examination.html', patient=patient)

@doctor_api.route('/examinations', methods=['POST'])
@login_required
def save_examination():
    try:
        # Parse JSON data from the request body
        data = request.get_json()
        print("Received data:", data)  # Debugging: Log the received data

        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        # Validate required fields
        patient_id = data.get('patient_id')
        examination_details = data.get('examination_details')
        print("Patient ID:", patient_id)  # Debugging: Log patient_id
        print("Examination Details:", examination_details)  # Debugging: Log examination_details

        if not patient_id or not examination_details:
            return jsonify({'success': False, 'message': 'Missing required fields: patient_id or examination_details'}), 400

        # Additional validation for nested fields
        if not examination_details.get('vitalSigns') or not examination_details.get('symptoms'):
            return jsonify({'success': False, 'message': 'Missing vital signs or symptoms in examination details'}), 400

        # Create the examination document
        examination = {
            'patient_id': ObjectId(patient_id),
            'doctor_id': ObjectId(current_user.id),
            'examination_details': examination_details,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }
        # Save to MongoDB
        result = mongo.db.examinations.insert_one(examination)

        # Create the medical record and link it to the examination
        medical_record = {
            'patientId': ObjectId(patient_id),
            'doctorId': ObjectId(current_user.id),
            'visitDate': datetime.now(),
            'examinationId': result.inserted_id,  # Link to the examination
            'vitalSigns': examination_details.get('vitalSigns', {}),
            'symptoms': examination_details.get('symptoms', []),
            'diagnosis': examination_details.get('diagnosis', []),
            'treatment': examination_details.get('treatment', {}),
            'notes': examination_details.get('notes', ''),
            'followUp': examination_details.get('followUp', {}),
            'createdAt': datetime.now(),
            'updatedAt': datetime.now()
        }
        mongo.db.medical_records.insert_one(medical_record)
        
        return jsonify({'success': True, 'message': 'Đã lưu hồ sơ khám và bệnh án thành công'}), 201
    except Exception as e:
        print(f"Error saving examination or medical record: {e}")
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500
@doctor_api.route('/doctor/medical-records', methods=['GET'])
@login_required
def render_medical_records_page():
    try:
        medical_records = list(mongo.db.medical_records.find())

        for record in medical_records:
            # Convert ObjectId to string
            record['_id'] = str(record['_id'])
            record['patientId'] = str(record.get('patientId', ''))
            record['doctorId'] = str(record.get('doctorId', ''))
            record['notes'] = record.get('notes', '')
            # Format dates
            record['visitDate'] = record['visitDate'].strftime('%Y-%m-%d') if record.get('visitDate') else None

            record['symptoms'] = record.get('symptoms', '')
            record['diagnosis'] = record.get('diagnosis', '')

            # Handle followUp
            record['followUp'] = record.get('followUp', {'required': False, 'recommendedDate': None, 'reason': ''})
            if record['followUp'].get('recommendedDate'):
                record['followUp']['recommendedDate'] = record['followUp']['recommendedDate'].strftime('%Y-%m-%d')

        return render_template('doctor/medical_records.html', medical_records=medical_records)
    except Exception as e:
        print(f"Error fetching medical records: {e}")
        return render_template('doctor/medical_records.html', medical_records=[])   