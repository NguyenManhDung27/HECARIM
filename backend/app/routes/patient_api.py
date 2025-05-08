from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user

from backend.app.utils.auth_utils import role_required
from ..extensions import mongo
from bson import ObjectId
from datetime import datetime, timedelta


patient_api = Blueprint('patient/api', __name__)



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

@patient_api.route('/timeslots/<doctor_id>/<date>', methods=['GET'])
@login_required
def get_available_timeslots(doctor_id, date):
    try:
        # Chuyển đổi ngày từ string sang datetime
        selected_date = datetime.strptime(date, '%Y-%m-%d')
        
        # Lấy lịch làm việc của bác sĩ
        doctor_schedule = mongo.db.doctor_schedules.find_one({
            '_id': ObjectId(doctor_id),
            'schedule.workDays': selected_date.strftime('%A')
        })

        if not doctor_schedule:
            return jsonify([])

        # Tạo danh sách các khung giờ từ lịch làm việc
        start_time = datetime.strptime(doctor_schedule['schedule']['workHours']['start'], '%H:%M')
        end_time = datetime.strptime(doctor_schedule['schedule']['workHours']['end'], '%H:%M')
        slot_duration = timedelta(minutes=30)  # Mỗi khung giờ 30 phút

        # Lấy danh sách cuộc hẹn đã đặt trong ngày
        booked_slots = set()
        appointments = mongo.db.appointments.find({
            'doctorId': ObjectId(doctor_id),
            'date': selected_date.date()
        })
        for appointment in appointments:
            booked_slots.add(appointment['timeSlot'])

        # Tạo danh sách các khung giờ còn trống
        available_slots = []
        current_slot = start_time
        while current_slot < end_time:
            slot_str = current_slot.strftime('%H:%M')
            if slot_str not in booked_slots:
                available_slots.append({'time': slot_str})
            current_slot += slot_duration

        return jsonify(available_slots)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@patient_api.route('/book_appointments', methods=['POST'])
@login_required
def book_appointment():
    try:
        data = request.get_json()
    
        # Kiểm tra dữ liệu đầu vào
        required_fields = ['department', 'doctor_id', 'date', 'time', 'symptoms']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Thiếu thông tin cần thiết'}), 400

        # Tạo cuộc hẹn mới
        appointment = {
            'patientId': str(current_user.user_data.get('patient_id')),
            'doctorId': ObjectId(data['doctor_id']),
            'department': data['department'],
            'date': datetime.strptime(data['date'], '%Y-%m-%d').date(),
            'timeSlot': data['time'],
            'symptoms': data['symptoms'],
            'status': 'pending',
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

        # Lưu vào database
        result = mongo.db.appointments.insert_one(appointment)
        
        return jsonify({
            'success': True,
            'message': 'Đặt lịch hẹn thành công',
            'appointment_id': str(result.inserted_id)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
# @role_required('patient')
def get_invoices():
    print("get_invoices")
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
    