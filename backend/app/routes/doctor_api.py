from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from ..extensions import mongo
from bson import ObjectId
from datetime import datetime

doctor_api = Blueprint('doctor/api', __name__)

@doctor_api.route('/prescriptions', methods=['POST'])
@login_required
def save_prescription():
    data = request.get_json()  # Lấy dữ liệu từ form gửi lên (JSON)
    print("Dữ liệu nhận được:", data)

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
    # if not data.get('patient_id') or not medications:
    #     return jsonify({'success': False, 'message': 'Thiếu thông tin bệnh nhân hoặc danh sách thuốc'}), 400

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

@doctor_api.route('/prescriptions', methods=['POST'])
@login_required
def save_examination():
    print("Patients loaded")
    pass