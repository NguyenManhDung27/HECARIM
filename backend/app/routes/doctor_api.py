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