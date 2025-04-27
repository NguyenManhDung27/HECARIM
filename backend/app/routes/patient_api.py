from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from ..extensions import mongo
from bson import ObjectId
from datetime import datetime, timedelta

patient_api = Blueprint('patient/api', __name__)

@patient_api.route('/doctors/<department_id>', methods=['GET'])
@login_required
def get_doctors_by_department(department_id):
    try:
        doctors = list(mongo.db.doctors.find({'departmentId': department_id}))
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
            'doctorId': ObjectId(doctor_id),
            'dayOfWeek': selected_date.strftime('%A').lower()
        })

        if not doctor_schedule:
            return jsonify([])

        # Tạo danh sách các khung giờ từ lịch làm việc
        start_time = datetime.strptime(doctor_schedule['startTime'], '%H:%M')
        end_time = datetime.strptime(doctor_schedule['endTime'], '%H:%M')
        slot_duration = timedelta(minutes=30)  # Mỗi khung giờ 30 phút

        # Lấy danh sách cuộc hẹn đã đặt trong ngày
        booked_slots = set()
        appointments = mongo.db.appointments.find({
            'doctorId': doctor_id,
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

@patient_api.route('/appointments', methods=['POST'])
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
            'doctorId': data['doctor_id'],
            'departmentId': data['department'],
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
            'patientId': str(current_user.user_data.get('patient_id'))
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
            'patientId': str(current_user.user_data.get('patient_id'))
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