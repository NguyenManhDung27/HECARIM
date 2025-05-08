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
    if 'medications' in data:
        for med in data['medications']:
            medications.append({
                'id': med.get('id'),
                'dosage': med.get('dosage'),
                'frequency': med.get('frequency'),
                'duration': med.get('duration'),
                'instructions': med.get('instructions')
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
    

# @doctor_api.route('/appointments/today', methods=['GET'])
# @login_required
# def get_today_appointments():
#     today = datetime.today()
#     start_of_day = datetime.combine(today.date(), datetime.min.time())
#     end_of_day = datetime.combine(today.date(), datetime.max.time())
#     appointments_list = mongo.db.appointments.find({
#         'doctorId': ObjectId(current_user.user_data.get('staff_id')), # Thay thế bằng ID bác sĩ thực tế
#         'appointmentTime': {'$gte': start_of_day, '$lte': end_of_day},
#     })
#     appointments=[]
#     for appt in appointments_list:
#         # Lấy thông tin bệnh nhân
#         patient = mongo.db.patients.find_one({'_id': ObjectId(appt['patientId'])})
#         # An toàn khi truy xuất thông tin
#         patient_name = patient['personalInfo']['fullName'] if patient else 'Không rõ'
#         appointments.append({
#             '_id': str(appt['_id']),
#             'patient_name': patient_name,
#             'patient_id': ObjectId(patient.get('patientId', '') if patient else ''),
#             'time': appt.get('timeSlot'),
#             'status': 'chờ khám',  # Hoặc trạng thái khác
#             'type': appt.get('type'),  # Hoặc trạng thái khác
#             'status_class': 'warning'  # hoặc tạo rule cho status_class theo trạng thái
#         })  
#     return jsonify(list(appointments))


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

        if not data:
            return jsonify({'success': False, 'message': 'No data provided'}), 400

        # Validate required fields
        patient_id = data.get('patient_id')
        examination_details = data.get('examination_details')

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

        # Remove the appointment from the database
        patientId=patient_id
        mongo.db.appointments.delete_one({'patientId': ObjectId(patientId)})
        
        return jsonify({'success': True, 'message': 'Đã lưu hồ sơ khám và bệnh án thành công'}), 201
    except Exception as e:
        print(f"Error saving examination or medical record: {e}")
        return jsonify({'success': False, 'message': f'An error occurred: {str(e)}'}), 500
@doctor_api.route('/doctor/medical-records/', methods=['GET'])
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
@doctor_api.route('/api/medical-records/<record_id>', methods=['GET'])
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
@doctor_api.route('/api/prescriptions/<prescription_id>', methods=['GET'])
@login_required
def get_prescription(prescription_id):
    try:
        # Fetch the prescription record
        prescription = mongo.db.prescriptions.find_one({'_id': ObjectId(prescription_id)})
        if not prescription:
            return jsonify({'error': 'Prescription not found'}), 404
#)
        # Convert ObjectId fields to strings
        prescription['_id'] = str(prescription['_id'])
        prescription['patient_id'] = str(prescription.get('patient_id', ''))
        prescription['doctor_id'] = str(prescription.get('doctor_id', ''))
        prescription['issue_date'] = prescription.get('issue_date').strftime('%Y-%m-%d') if prescription.get('issue_date') else None

        # Fetch patient and doctor names
        patient = mongo.db.patients.find_one({'_id': ObjectId(prescription['patient_id'])})
        prescription['patient_name'] = patient['personalInfo']['fullName'] if patient else "N/A"

        # Find the user first
        user = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})

        # Then use the staff_id from the user to find the doctor
        doctor = mongo.db.doctors.find_one({'_id': user['staff_id']}) if user else None

        # Assign the doctor's name to the prescription
        prescription['doctor_name'] = doctor['personalInfo']['fullName'] if doctor else "N/A"

        # Fetch medication names from medications collection
        for med in prescription.get('medications', []):
            med['medicationId'] = med.get('id', "")
            med['dosage'] = med.get('dosage', "N/A")
            med['frequency'] = med.get('frequency', "N/A")
            med['duration'] = med.get('duration', "N/A")
            medication = mongo.db.medications.find_one({'_id': ObjectId(med.get('id', ""))})
            med['name'] = medication['name'] if medication else "N/A"
            med['instructions'] = med.get('instructions', "N/A")  # Add this line
        return jsonify(prescription), 200

    except Exception as e:
        print(f"Error fetching prescription: {e}")
        return jsonify({'error': 'An error occurred'}), 500
@doctor_api.route('/schedule', methods=['GET'])
@login_required
def get_schedule():
    try:
        # Find the logged-in doctor
        user = mongo.db.users.find_one({'_id': ObjectId(current_user.id)})
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        doctor = mongo.db.doctors.find_one({'_id': user['staff_id']})
        if not doctor:
            return jsonify({"success": False, "message": "Doctor not found"}), 404


        selected_date_str = request.args.get("date")
        if not selected_date_str:
            return jsonify({"success": False, "message": "Date parameter is missing"}), 400  # Return an error if date is missing

        selected_date = datetime.strptime(selected_date_str, "%Y-%m-%d")
        start_of_day = datetime.combine(selected_date, datetime.min.time())
        end_of_day = datetime.combine(selected_date, datetime.max.time())

        appointments_cursor = mongo.db.appointments.find({
            "doctorId": ObjectId(str(doctor['_id'])),
            "appointmentTime": {"$gte": start_of_day, "$lt": end_of_day}  # Proper date filtering
        })



        appointments = list(appointments_cursor)
        appointments_by_date = {}

        # Format appointments for frontend
        formatted_appointments = []
        for appointment in appointments:
            formatted_appointments.append({
                "id": str(appointment["_id"]),
                "patient_id": str(appointment["patientId"]),
                "date": appointment["appointmentTime"].strftime('%Y-%m-%d'),
                "time": appointment["timeSlot"],
                "status": appointment["status"]
            })

        appointments_by_date = {}

        for appointment in appointments:
            date_key = appointment["appointmentTime"].strftime('%Y-%m-%d')
            if date_key not in appointments_by_date:
                appointments_by_date[date_key] = []
            appointments_by_date[date_key].append(appointment["timeSlot"])

        return jsonify({"success": True, "appointments": formatted_appointments, "appointments_by_date": appointments_by_date}), 200

    except Exception as e:
        print(f"Error fetching schedule: {e}")
        return jsonify({"success": False, "message": "Có lỗi xảy ra khi lấy lịch khám"}), 500
