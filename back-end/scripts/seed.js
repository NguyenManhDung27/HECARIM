const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');
const dotenv = require('dotenv');

// Load models
const User = require('../models/user.model');
const Patient = require('../models/patient.model');
const Doctor = require('../models/doctor.model');
const Appointment = require('../models/appointment.model');
const MedicalRecord = require('../models/medicalRecord.model');
const Receptionist = require('../models/receptionist.model');
const Medication = require('../models/medication.model');
const Service = require('../models/service.model');
const Invoice = require('../models/invoice.model');
const Department = require('../models/department.model');
const Prescription = require('../models/prescription.model');

dotenv.config();

// Kết nối MongoDB
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/hecarim', {
    useNewUrlParser: true,
    useUnifiedTopology: true
});

// Hàm tạo mật khẩu hash
const hashPassword = async (password) => {
    const salt = await bcrypt.genSalt(10);
    return bcrypt.hash(password, salt);
};

// Dữ liệu mẫu
const seedData = async () => {
    try {
        // Xóa dữ liệu cũ
        await mongoose.connection.dropDatabase();
        console.log('Đã xóa dữ liệu cũ');

        // Tạo bác sĩ
        const doctor = await Doctor.create({
            doctorId: 'DR001',
            personalInfo: {
                fullName: 'Trần Văn B',
                gender: 'male',
                dateOfBirth: new Date('1980-01-01'),
                idNumber: '123456789012',
                address: '123 Đường ABC, Quận 1, TP.HCM',
                phone: '0987654321',
                email: 'doctor@example.com'
            },
            professionalInfo: {
                specialization: 'Nội Tổng Quát',
                qualification: ['Tiến sĩ Y khoa', 'Thạc sĩ Y học Cơ sở'],
                licenseNumber: 'LICENSE001',
                experience: 15,
                department: 'Nội Tổng Quát'
            },
            schedule: {
                workDays: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                workHours: {
                    start: '08:00',
                    end: '17:00'
                }
            }
        });

        // Tạo khoa
        const department = await Department.create({
            departmentId: 'DEPT001',
            name: 'Nội Tổng Quát',
            description: 'Khoa khám và điều trị các bệnh nội khoa tổng quát',
            head: doctor._id,
            location: 'Tầng 2, Tòa nhà A',
            contactNumber: '028.1234567',
            status: 'active',
            capacity: {
                maxPatients: 100,
                maxDoctors: 10
            },
            staff: {
                doctors: [doctor._id]
            }
        });

        // Tạo dịch vụ
        const service = await Service.create({
            serviceId: 'SV001',
            name: 'Khám Tổng Quát',
            category: 'Khám tổng quát',
            description: 'Khám sức khỏe tổng quát định kỳ',
            duration: 30,
            price: 500000,
            department: department._id,
            status: 'active'
        });

        // Tạo thuốc
        const medication = await Medication.create({
            medicationId: 'MED001',
            name: 'Paracetamol',
            genericName: 'Acetaminophen',
            category: 'Giảm đau, hạ sốt',
            manufacturer: 'Công ty Dược ABC',
            description: 'Thuốc giảm đau, hạ sốt thông thường',
            dosageForm: 'Viên',
            strength: '500mg',
            usageInstructions: 'Uống sau ăn',
            price: 2000,
            stock: {
                quantity: 1000,
                batchNumber: 'BATCH001',
                expiryDate: new Date('2025-12-31')
            }
        });

        // Tạo bệnh nhân
        const patient = await Patient.create({
            patientId: 'PT001',
            personalInfo: {
                fullName: 'Nguyễn Văn A',
                gender: 'male',
                dateOfBirth: new Date('1990-01-01'),
                idNumber: '123456789014',
                address: '456 Đường XYZ, Quận 2, TP.HCM',
                phone: '0123456789',
                email: 'patient@example.com',
                emergencyContact: {
                    name: 'Nguyễn Thị B',
                    relationship: 'Vợ',
                    phone: '0123456788'
                }
            },
            healthInfo: {
                bloodType: 'O+',
                allergies: ['Penicillin'],
                chronicDiseases: [],
                height: 170,
                weight: 65
            },
            insurance: {
                provider: 'BHYT',
                policyNumber: 'BH123456789',
                expiryDate: new Date('2025-12-31')
            }
        });

        // Tạo lễ tân
        const receptionist = await Receptionist.create({
            staffId: 'RC001',
            personalInfo: {
                fullName: 'Lê Thị C',
                gender: 'female',
                dateOfBirth: new Date('1992-05-15'),
                idNumber: '123456789013',
                address: '789 Đường DEF, Quận 3, TP.HCM',
                phone: '0987654322',
                email: 'receptionist@example.com'
            },
            employmentInfo: {
                joinDate: new Date('2020-01-01'),
                shift: 'Sáng',
                status: 'active'
            }
        });

        // Tạo tài khoản người dùng
        const doctorUser = await User.create({
            username: 'doctor',
            passwordHash: await hashPassword('password'),
            role: 'doctor',
            staffId: doctor._id,
            status: 'active'
        });

        const receptionistUser = await User.create({
            username: 'receptionist',
            passwordHash: await hashPassword('password'),
            role: 'receptionist',
            staffId: receptionist._id,
            status: 'active'
        });

        // Tạo lịch hẹn
        const appointment = await Appointment.create({
            appointmentId: 'APT001',
            patientId: patient._id,
            doctorId: doctor._id,
            appointmentDate: new Date('2025-04-20'),
            timeSlot: {
                start: new Date('2025-04-20T09:00:00Z'),
                end: new Date('2025-04-20T09:30:00Z')
            },
            status: 'scheduled',
            type: 'new',
            reason: 'Khám tổng quát',
            createdBy: receptionistUser._id
        });

        // Tạo hồ sơ y tế
        const medicalRecord = await MedicalRecord.create({
            recordId: 'MR001',
            patientId: patient._id,
            visitDate: new Date('2025-04-20'),
            doctorId: doctor._id,
            vitalSigns: {
                temperature: 37.5,
                bloodPressure: {
                    systolic: 120,
                    diastolic: 80
                },
                heartRate: 75,
                respiratoryRate: 16
            },
            symptoms: ['Đau đầu', 'Sốt nhẹ'],
            diagnosis: ['Viêm đường hô hấp trên'],
            treatment: {
                medications: [{
                    medicationId: medication._id,
                    name: 'Paracetamol',
                    dosage: '500mg',
                    frequency: '2 lần/ngày',
                    duration: '5 ngày',
                    instructions: 'Uống sau ăn'
                }],
                procedures: [{
                    serviceId: service._id,
                    name: 'Khám Tổng Quát',
                    notes: 'Khám theo quy trình chuẩn',
                    results: 'Sức khỏe ổn định'
                }]
            },
            followUp: {
                required: true,
                recommendedDate: new Date('2025-04-27'),
                reason: 'Tái khám sau 1 tuần'
            }
        });

        // Tạo đơn thuốc
        const prescription = await Prescription.create({
            prescriptionId: 'RX001',
            patientId: patient._id,
            doctorId: doctor._id,
            issueDate: new Date('2025-04-20'),
            medications: [{
                medicationId: medication._id,
                name: 'Paracetamol',
                dosage: '500mg',
                frequency: '2 lần/ngày',
                duration: '5 ngày',
                quantity: 10,
                instructions: 'Uống sau ăn'
            }],
            status: 'active',
            validUntil: new Date('2025-04-27')
        });

        // Tạo hóa đơn
        const invoice = await Invoice.create({
            invoiceId: 'INV001',
            patientId: patient._id,
            appointmentId: appointment._id,
            issueDate: new Date('2025-04-20'),
            items: [
                {
                    type: 'Dịch vụ',
                    itemId: service._id,
                    name: 'Khám Tổng Quát',
                    quantity: 1,
                    unitPrice: 500000,
                    totalPrice: 500000
                },
                {
                    type: 'Thuốc',
                    itemId: medication._id,
                    name: 'Paracetamol',
                    quantity: 10,
                    unitPrice: 2000,
                    totalPrice: 20000
                }
            ],
            subtotal: 520000,
            tax: 52000,
            grandTotal: 572000,
            status: 'pending',
            issuedBy: receptionistUser._id
        });

        console.log('Đã tạo dữ liệu mẫu thành công');
        console.log('Tài khoản mẫu:');
        console.log('Bác sĩ - username: doctor, password: password');
        console.log('Lễ tân - username: receptionist, password: password');

    } catch (error) {
        console.error('Lỗi khi tạo dữ liệu mẫu:', error);
    } finally {
        mongoose.disconnect();
    }
};

// Chạy seeder
seedData();