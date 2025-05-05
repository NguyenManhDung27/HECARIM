from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from ..extensions import mongo
from bson import ObjectId
from datetime import datetime

doctor_bp = Blueprint('doctor', __name__)

@doctor_bp.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'total_appointments': 12,
        'checked_in': 5,
        'waiting': 4,
        'completed': 3
    }
    appointments = []
    # Lấy thông tin bác sĩ từ cơ sở dữ liệu
    today = datetime.today()
    start_of_day = datetime.combine(today.date(), datetime.min.time())
    end_of_day = datetime.combine(today.date(), datetime.max.time())
    appointments_list = mongo.db.appointments.find({
        'doctorId': str(current_user.user_data.get('staff_id')), # Thay thế bằng ID bác sĩ thực tế
        'appointmentTime': {'$gte': start_of_day, '$lte': end_of_day},
    })
    for appt in appointments_list:
        # Lấy thông tin bệnh nhân
        patient = mongo.db.patients.find_one({'_id': ObjectId(appt['patientId'])})
        # An toàn khi truy xuất thông tin
        patient_name = patient['personalInfo']['fullName'] if patient else 'Không rõ'
        appointments.append({
            'patient_name': patient_name,
            'patient_id': patient.get('patientId', '') if patient else '',
            'time': appt.get('timeSlot'),
            'status': 'chờ khám',  # Hoặc trạng thái khác
            'type': appt.get('type'),  # Hoặc trạng thái khác
            'status_class': 'warning'  # hoặc tạo rule cho status_class theo trạng thái
        })    
    return render_template(
        'doctor/dashboard.html',
        stats=stats,
        notifications_count=3,  # hoặc context processor như đã nói
        today=today,
    )
        # appointments=appointments,  # Truyền danh sách cuộc hẹn vào template


@doctor_bp.route('/medical-records')
@login_required
def medical_records():
        # Get the current page from the query parameters (default to 1)
    page = int(request.args.get('page', 1))
    if page < 1:
        page = 1  # Ensure page is at least 1

    per_page = 5  # Number of records per page

    patients = list(mongo.db.patients.find())
    for patient in patients:
        patient['_id'] = str(patient['_id']) 
    # Fetch medical records with pagination
    total_records = mongo.db.medical_records.count_documents({})
    medical_records = list(
        mongo.db.medical_records.find()
        .skip((page - 1) * per_page)
        .limit(per_page)
    )
    patient_map = {str(patient['_id']): patient['personalInfo']['fullName'] for patient in patients}

    # Process the records (convert ObjectId to string, format dates, etc.)
    for record in medical_records:
        record['_id'] = str(record['_id'])
        record['patientId'] = str(record.get('patientId', ''))
        record['doctorId'] = str(record.get('doctorId', ''))
        record['patient_name'] = patient_map.get(record['patientId'], 'Không xác định')
        record['visitDate'] = record['visitDate'].strftime('%Y-%m-%d')
        record['symptoms'] = record.get('symptoms', '')
        record['diagnosis'] = record.get('diagnosis', '')
        record['notes'] = record.get('notes', '')
    # Calculate total pages
    total_pages = (total_records + per_page - 1) // per_page  # Round up division
    # Pass the processed records to the template
    return render_template(
        'doctor/medical_records.html',
        medical_records=medical_records,
        notifications_count=3,
        page=page,
        total_pages=total_pages,
        has_prev=page > 1,
        has_next=page < total_pages,
    )
@doctor_bp.route('/prescriptions')
@login_required
def prescriptions():
    print("Patients loaded")
    patients =list(mongo.db.patients.find())
    for patient in patients:
        patient['_id'] = str(patient['_id'])  # Chuyển đổi ObjectId thành chuỗi
    # patients = list(patients)  # Chuyển đổi cursor thành danh sách
    medications = list(mongo.db.medications.find())
    prescriptions = list(mongo.db.prescriptions.find())

    # Tạo dictionary ánh xạ `patient_id` -> `patient_name`
    patient_map = {str(patient['_id']): patient['personalInfo']['fullName'] for patient in patients}

# Chuyển đổi ObjectId thành chuỗi và thêm `patient_name` vào mỗi đơn thuốc
    for prescription in prescriptions:
        prescription['_id'] = str(prescription['_id'])
        prescription['patient_id'] = str(prescription['patient_id'])
        prescription['doctor_id'] = str(prescription['doctor_id'])
        prescription['issue_date'] = prescription['issue_date'].strftime('%Y-%m-%d')  # Định dạng ngày
        prescription['patient_name'] = patient_map.get(prescription['patient_id'], 'Không xác định')  # Lấy tên bệnh nhân
        # print
    today = datetime.today()
    return render_template('doctor/prescriptions.html',
                            notifications_count =3,
                            today=today,
                            patients=patients,
                            medications=medications,
                            prescriptions=prescriptions)

@doctor_bp.route('/patients')
@login_required
def patients():
    page = request.args.get('page', 1, type=int)  # Lấy số trang từ query string, mặc định là 1
    per_page = 10  # Số lượng bệnh nhân trên mỗi trang
    if page < 1:
        page = 1  # Đảm bảo số trang không nhỏ hơn 1

    # Đếm tổng số bệnh nhân
    total_patients = mongo.db.patients.count_documents({})  # Đếm tất cả bệnh nhân

    # Lấy danh sách bệnh nhân với phân trang
    patients_cursor = mongo.db.patients.find().skip((page - 1) * per_page).limit(per_page)

    # Tính toán tổng số trang
    total_pages = (total_patients + per_page - 1) // per_page
    # Kiểm tra xem có trang trước và trang sau không
    has_prev = page > 1
    has_next = page < total_pages

    return render_template(
        'doctor/patients.html',
        patients=list(patients_cursor),
        page=page,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        notifications_count=3
    )
@doctor_bp.route('/patient/<string:patient_id>')
@login_required
def patient_details(patient_id):
    patient = mongo.db.patients.find_one({'_id': ObjectId(patient_id)})
    if not patient:
        return "Patient not found", 404
    return render_template('doctor/patient_details.html', patient=patient)

# @doctor_bp.route('/examination/<appointment_id>')
# @login_required
# def examination(appointment_id):
#     appointment = mongo.db.appointments.find_one({'_id': ObjectId(appointment_id)})
#     if not appointment:
#         return "Appointment not found", 404
#     return render_template('doctor/examination.html', appointment=appointment)

@doctor_bp.route('/examination/<patient_id>', methods=['GET'])
@login_required
def examination(patient_id):
    # Truy vấn thông tin bệnh nhân từ MongoDB
    patient = mongo.db.patients.find_one({'patientId': patient_id})
    if not patient:
        return "Patient not found", 404

    # Chuyển đổi ObjectId thành chuỗi
    patient['_id'] = str(patient['_id'])

    # Truy vấn danh sách thuốc
    medications = list(mongo.db.medications.find())
    for med in medications:
        med['_id'] = str(med['_id'])

    # Render template với thông tin bệnh nhân và danh sách thuốc
    return render_template('doctor/examination.html',
                            patient=patient,
                            medications=medications,
                            notifications_count=3)

@doctor_bp.route('/profile')
@login_required
def profile():
    doctor = mongo.db.doctors.find_one({'_id': current_user.user_data.get('staff_id')})
    if not doctor:
        return "Doctor profile not found", 404
    return render_template('doctor/profile.html', doctor=doctor, notifications_count = 3)
@doctor_bp.route('/schedule-page')
@login_required
def schedule_page():
    return render_template("doctor/schedule.html", notifications_count = 3)

