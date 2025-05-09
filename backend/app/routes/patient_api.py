from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from flask_mail import Mail, Message

from backend.app.utils.auth_utils import role_required
from backend.app import mongo, mail
from bson import ObjectId
from datetime import datetime, timedelta
import sys
import os
import pandas as pd
import numpy as np

# Thêm thư mục gốc vào sys.path để có thể import module từ AI/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))
from AI.test import load_data, preprocess_data, train_decision_tree, predict_disease, fuzzy_match

# mail = Mail()
patient_api = Blueprint('patient_api', __name__)

# Tải và khởi tạo mô hình AI lúc khởi động ứng dụng
try:
    ai_model = None
    symptom_names = None
    
    def initialize_ai_model():
        global ai_model, symptom_names
        # Đường dẫn tương đối từ thư mục hiện tại đến file dataset.csv
        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../AI/dataset.csv'))
        data = load_data(file_path)
        if data is not None:
            disease_names, symptoms_data, symptom_names = preprocess_data(data)
            ai_model = train_decision_tree(symptoms_data, disease_names)
            return True
        return False
    
    # Khởi tạo mô hình khi server khởi động
    model_initialized = initialize_ai_model()
except Exception as e:
    print(f"Lỗi khi khởi tạo mô hình AI: {e}")
    model_initialized = False

@patient_api.route('/predict_from_text', methods=['POST'])
@login_required
def predict_from_text():
    global ai_model, symptom_names
    
    # Kiểm tra xem mô hình đã được khởi tạo chưa
    if ai_model is None or symptom_names is None:
        success = initialize_ai_model()
        if not success:
            return jsonify({
                'success': False,
                'message': 'Không thể khởi tạo mô hình AI. Vui lòng liên hệ quản trị viên.'
            }), 500
    
    try:
        data = request.get_json()
        symptoms_text = data.get('symptoms_text', '')
        
        if not symptoms_text:
            return jsonify({
                'success': False,
                'message': 'Không có triệu chứng được cung cấp'
            }), 400
        
        # Tách chuỗi triệu chứng dựa trên dấu phẩy
        input_symptoms = [s.strip() for s in symptoms_text.split(',') if s.strip()]
        
        if not input_symptoms:
            return jsonify({
                'success': False,
                'message': 'Không có triệu chứng được cung cấp sau khi xử lý'
            }), 400
        
        # Thực hiện fuzzy matching cho mỗi triệu chứng nhập vào
        matched_symptoms = []
        for symptom in input_symptoms:
            matches = fuzzy_match(symptom, symptom_names, threshold=0.5)
            if matches:
                # Thêm triệu chứng khớp nhất vào danh sách
                matched_symptoms.append(matches[0][0])
        
        if not matched_symptoms:
            return jsonify({
                'success': False,
                'message': 'Không thể tìm thấy triệu chứng phù hợp trong cơ sở dữ liệu'
            }), 400
        
        # Dự đoán bệnh dựa trên các triệu chứng đã khớp
        predictions = predict_disease(ai_model, matched_symptoms, symptom_names)
        
        # Lọc ra các dự đoán có xác suất > 0 và lấy top 5
        filtered_predictions = [
            {
                'disease': disease,
                'probability': round(float(probability) * 100, 2)
            }
            for disease, probability in predictions[:5]
            if probability > 0
        ]
        
        return jsonify({
            'success': True,
            'matched_symptoms': matched_symptoms,
            'predictions': filtered_predictions
        })
        
    except Exception as e:
        print(f"Lỗi khi dự đoán bệnh: {e}")
        return jsonify({
            'success': False,
            'message': 'Đã xảy ra lỗi khi dự đoán. Vui lòng thử lại.'
        }), 500

@patient_api.route('/doctors/<department>', methods=['GET'])
@login_required
def get_doctors_by_department(department):
    try:
        # Lấy danh sách bác sĩ theo khoa
        doctors = list(mongo.db.doctors.find({'professionalInfo.department': 'Khoa Nội'}))
        # Chỉ trả về thông tin cần thiết
        doctor_list = [{
            'id': str(doctor['_id']),
            'name': doctor['personalInfo']['fullName'],
            'specialization': doctor.get('specialization', '')
        } for doctor in doctors]
        return jsonify(doctor_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@patient_api.route('/appointments', methods=['POST']) 
@login_required 
def book_appointment(): 
    data = request.get_json() 
    print(data)
    appointment_data = {
    'patientId': ObjectId(current_user.user_data.get('patient_id')),
    'doctorId': ObjectId(data['doctor_id']),
    'appointmentTime': datetime.strptime(data['appointment_date'], '%Y-%m-%d'),
    'timeSlot': data['time_slot'],
    'status': 'đã lên lịch',
    'type': data.get('type', ''),
    'notes': data.get('notes', ''),
    'reason': data.get('reason', ''),
    'createdAt': datetime.now(),
    'updatedAt': datetime.now()
    }
    # Lưu vào database 
    try:
        mongo.db.appointments.insert_one(appointment_data)
        patient = mongo.db.patients.find_one({'_id': ObjectId(current_user.user_data.get('patient_id'))})
        if not patient:
            return jsonify({'error': 'Không tìm thấy bệnh nhân'}), 404
        # Gửi email xác nhận lịch hẹn
        try:
            msg = Message(
                subject='Xác nhận lịch hẹn',
                recipients=[patient['personalInfo']['email']]
            )
            msg.html = f"""
                <h1>Xin chào {patient['personalInfo']['fullName']}</h1>
                <p>Lịch hẹn của bạn đã được đặt thành công.</p>
                <p><strong>Thời gian:</strong> {data['appointment_date']} - {data['time_slot']}</p>
                <p><strong>Loại khám:</strong> {data.get('type', 'Không có')}</p>
                <p><strong>Lý do:</strong> {data.get('reason', 'Không có')}</p>
                <p>Cảm ơn bạn đã sử dụng dịch vụ của chúng tôi!</p>
            """
            mail.send(msg)
            print("Email xác nhận đã được gửi thành công")
            return jsonify({    "success": True,"message": "Lịch hẹn đã được tạo thành công"})
        except Exception as e:
            print(f'Lỗi khi gửi email xác nhận lịch hẹn: {e}')
            return jsonify({'success': False, 'message': 'Đã xảy ra lỗi khi gửi email xác nhận.'}), 500
    except Exception as e:
        return jsonify({'error': 'Internal Server Error'}), 500

@patient_api.route('/appointments/<appointment_id>', methods=['DELETE'])
@login_required
def cancel_appointment(appointment_id):
    try:
        # Kiểm tra quyền hủy lịch
        appointment = mongo.db.appointments.find_one({
            '_id': ObjectId(appointment_id),
            'patientId': ObjectId(current_user.user_data.get('patient_id'))
        })
        
        if not appointment:
            return jsonify({'error': 'Không tìm thấy lịch hẹn'}), 404

        if appointment['status'] not in ['pending', 'confirmed']:
            return jsonify({'error': 'Không thể hủy lịch hẹn này'}), 400

        # Cập nhật trạng thái
        mongo.db.appointments.update_one(
            {'_id': ObjectId(appointment_id)},
            {
                '$set': {
                    'status': 'cancelled',
                    'updated_at': datetime.now()
                }
            }
        )

        return jsonify({
            'success': True,
            'message': 'Đã hủy lịch hẹn thành công'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@patient_api.route('/appointments/<appointment_id>', methods=['PATCH'])
@login_required
def reschedule_appointment(appointment_id):
    try:
        data = request.get_json()
        
        # Kiểm tra dữ liệu đầu vào
        if not all(field in data for field in ['date', 'time']):
            return jsonify({'error': 'Thiếu thông tin cần thiết'}), 400

        # Kiểm tra quyền đổi lịch
        appointment = mongo.db.appointments.find_one({
            '_id': ObjectId(appointment_id),
            'patientId': ObjectId(current_user.user_data.get('patient_id'))
        })
        
        if not appointment:
            return jsonify({'error': 'Không tìm thấy lịch hẹn'}), 404

        if appointment['status'] not in ['pending', 'confirmed']:
            return jsonify({'error': 'Không thể đổi lịch hẹn này'}), 400

        # Cập nhật thời gian mới
        mongo.db.appointments.update_one(
            {'_id': ObjectId(appointment_id)},
            {
                '$set': {
                    'date': datetime.strptime(data['date'], '%Y-%m-%d').date(),
                    'timeSlot': data['time'],
                    'status': 'pending',  # Reset status về pending
                    'updated_at': datetime.now()
                }
            }
        )

        return jsonify({
            'success': True,
            'message': 'Đã cập nhật lịch hẹn thành công'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@patient_api.route('/profile', methods=['PATCH'])
@login_required
def update_profile():
    try:
        data = request.get_json()
        
        # Cập nhật thông tin cá nhân
        mongo.db.patients.update_one(
            {'_id': ObjectId(current_user.user_data.get('patient_id'))},
            {
                '$set': {
                    'personalInfo.phone': data.get('phone'),
                    'personalInfo.address': data.get('address'),
                    'personalInfo.emergencyContact': data.get('emergency_contact'),
                    'updated_at': datetime.now()
                }
            }
        )

        return jsonify({
            'success': True,
            'message': 'Đã cập nhật thông tin thành công'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@patient_api.route('/records/<record_id>', methods=['GET'])
@login_required
def get_medical_record(record_id):
    try:
        # Fetch the medical record from the database
        record = mongo.db.medical_records.find_one({'_id': ObjectId(record_id)})
        if not record:
            return jsonify({'error': 'Medical record not found'}), 404

        # Convert ObjectId to string and format fields
        record['_id'] = str(record['_id'])
        record['patientId'] = str(record.get('patientId', ''))
        record['doctorId'] = str(record.get('doctorId', ''))
        record['visitDate'] = record['visitDate'].strftime('%Y-%m-%d') if record.get('visitDate') else None
        record['examinationId'] = str(record.get('examinationId', ''))
        # Add patient name (fetch from patients collection if needed)
        patient = mongo.db.patients.find_one({'_id': ObjectId(record['patientId'])})
        record['patient_name'] = patient['personalInfo']['fullName'] if patient else "N/A"


        # Add vital signs
        record['vital_signs'] = {
            'temperature': record.get('vitalSigns', {}).get('temperature', "N/A"),
            'blood_pressure': record.get('vitalSigns', {}).get('bloodPressure', {'systolic': "N/A", 'diastolic': "N/A"}),
            'heart_rate': record.get('vitalSigns', {}).get('heartRate', "N/A"),
            'respiratoryRate': record.get('vitalSigns', {}).get('respiratoryRate', "N/A")
        }

        record['symptoms'] = record.get('symptoms', '')
        record['diagnosis'] = record.get('diagnosis', '')
        record['notes'] = record.get('notes', '')

        # Add treatment details
        record['treatment'] = record.get('treatment', {'recommendations': '', 'medications': []})
        for med in record['treatment']['medications']:
            med['medicationId'] = med.get('medicationId', "")
            med['dosage'] = med.get('dosage', "N/A")
            med['frequency'] = med.get('frequency', "N/A")
            med['duration'] = med.get('duration', "N/A")
            med['instructions'] = med.get('instructions', "N/A")
            medication = mongo.db.medications.find_one({'_id': ObjectId(med.get('medicationId', ""))})
            med['name'] = medication.get('name', "N/A")




        record['followUp'] = record.get('followUp', {'required': False, 'recommendedDate': None, 'reason': ''})
        if record['followUp'].get('recommendedDate'):
            record['followUp']['recommendedDate'] = record['followUp']['recommendedDate'].strftime('%Y-%m-%d')

        return jsonify(record), 200
    except Exception as e:
        print(f"Error fetching medical record: {e}")
        return jsonify({'error': 'An error occurred'}), 500
    
@patient_api.route('/invoices/details/<invoice_id>', methods=['GET'])
@login_required
@role_required('patient')
def get_invoice_details(invoice_id):
    try:
        # Tìm hóa đơn theo ID
        invoice = mongo.db.invoices.find_one({'_id': ObjectId(invoice_id)})
        if not invoice:
            return jsonify({'success': False, 'message': 'Hóa đơn không tồn tại'}), 404

        # Chuyển đổi ObjectId sang chuỗi
        invoice['_id'] = str(invoice['_id'])
        invoice['patientId'] = str(invoice['patientId'])
        if invoice.get('appointmentId'):
            invoice['appointmentId'] = str(invoice['appointmentId'])
        if invoice.get('issuedBy'):
            invoice['issuedBy'] = str(invoice['issuedBy'])
        # Truy vấn thông tin bệnh nhân
        patient = mongo.db.patients.find_one({'_id': ObjectId(invoice['patientId'])})
        invoice['patientName'] = patient['personalInfo']['fullName'] if patient else 'Không xác định'

        # Trả về chi tiết hóa đơn
        return jsonify({'success': True, 'invoice': invoice}), 200

    except Exception as e:
        print(f'Lỗi khi lấy chi tiết hóa đơn: {e}')
        return jsonify({'success': False, 'message': 'Đã xảy ra lỗi khi lấy chi tiết hóa đơn'}), 500
    
@patient_api.route('/invoices', methods=['GET'])
@login_required
@role_required('patient')
def invoices():
    try:
        invoices = mongo.db.invoices.find({'patientId': ObjectId(current_user.user_data.get('patient_id'))})
        result = []
        for invoice in invoices:
            invoice['_id'] = str(invoice['_id'])
            invoice['patientId'] = str(invoice['patientId'])
            
            # Truy vấn tên bệnh nhân từ collection patients
            patient = mongo.db.patients.find_one({'_id': ObjectId(invoice['patientId'])})
            invoice['patientName'] = patient['personalInfo']['fullName'] if patient else 'Không xác định'
            # print(invoice['patientName'])
            if invoice.get('appointmentId'):
                invoice['appointmentId'] = str(invoice['appointmentId'])
            invoice['issuedBy'] = str(invoice['issuedBy'])
            result.append(invoice)

        return jsonify({'success': True, 'invoices': result}), 200

    except Exception as e:
        print(f'Lỗi khi lấy danh sách hóa đơn: {e}')
        return jsonify({'success': False, 'message': 'Đã xảy ra lỗi khi lấy danh sách hóa đơn'}), 500
