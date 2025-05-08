COLLECTION: Patient

{
  _id: ObjectId,
  patientId: String,  // Mã bệnh nhân
  personalInfo: {
    fullName: String,
    gender: String,
    dateOfBirth: Date,
    idNumber: String,  // CCCD/CMND
    address: String,
    phone: String,
    email: String,
    emergencyContact: {
      name: String,
      relationship: String,
      phone: String
    }
  },
  healthInfo: {
    bloodType: String,
    allergies: [String],
    chronicDiseases: [String],
    familyMedicalHistory: String,
    height: Number,
    weight: Number
  },
  medicalHistory: [
    {
      diagnosisDate: Date,
      symptoms: [String],
      diagnosis: String,
      treatment: String,
      doctor: ObjectId,  // Tham chiếu đến bác sĩ
      notes: String
    }
  ],
  insurance: {
    provider: String,
    policyNumber: String,
    expiryDate: Date
  },
  createdAt: Date,
  updatedAt: Date
}

COLLECTION: Doctor

{
  _id: ObjectId,
  doctorId: String,  // Mã bác sĩ
  personalInfo: {
    fullName: String,
    gender: String,
    dateOfBirth: Date,
    idNumber: String,
    address: String,
    phone: String,
    email: String
  },
  professionalInfo: {
    specialization: String,
    qualification: [String],
    licenseNumber: String,
    experience: Number,  // Số năm kinh nghiệm
    department: String
  },
  schedule: {
    workDays: [String],  // Các ngày làm việc trong tuần
    workHours: {
      start: String,
      end: String
    },
    vacationDates: [Date]
  },
  createdAt: Date,
  updatedAt: Date
}

COLLECTION: Appointments

{
  _id: ObjectId,
  appointmentId: String,
  patientId: ObjectId,  // Tham chiếu đến bệnh nhân
  doctorId: ObjectId,   // Tham chiếu đến bác sĩ
  appointmentDate: Date,
  timeSlot: {
    start: Date,
    end: Date
  },
  status: String,  // Đã đặt, Hoàn thành, Hủy, Vắng mặt
  type: String,    // Khám lần đầu, Tái khám
  reason: String,
  symptoms: [String],
  notes: String,
  createdBy: ObjectId,  // Người tạo lịch hẹn (có thể là tiếp tân)
  createdAt: Date,
  updatedAt: Date
}

COLLECTION: Receptionists

{
  _id: ObjectId,
  staffId: String,
  personalInfo: {
    fullName: String,
    gender: String,
    dateOfBirth: Date,
    idNumber: String,
    address: String,
    phone: String,
    email: String
  },
  employmentInfo: {
    joinDate: Date,
    shift: String,  // Ca sáng, ca chiều
    status: String  // Đang làm việc, Nghỉ việc
  },
  accountInfo: {
    username: String,
    passwordHash: String,
    role: String,
    lastLogin: Date
  },
  createdAt: Date,
  updatedAt: Date
}

COLLECTION: Medications

{
  _id: ObjectId,
  medicationId: String,
  name: String,
  genericName: String,
  category: String,
  manufacturer: String,
  description: String,
  dosageForm: String,  // Viên, Siro, Ống tiêm...
  strength: String,    // Hàm lượng
  usageInstructions: String,
  sideEffects: [String],
  contraindications: [String],
  price: Number,
  stock: {
    quantity: Number,
    batchNumber: String,
    expiryDate: Date
  },
  createdAt: Date,
  updatedAt: Date
}

COLLECTION: Services

{
  _id: ObjectId,
  serviceId: String,
  name: String,
  category: String,  // Khám tổng quát, Nội soi, Xét nghiệm...
  description: String,
  duration: Number,  // Thời gian dự kiến (phút)
  price: Number,
  requiredEquipment: [String],
  preparationInstructions: String,
  department: String,
  status: String,  // Hoạt động, Tạm ngưng
  createdAt: Date,
  updatedAt: Date
}

COLLECTION: Invoice

{
  _id: ObjectId,
  invoiceId: String,
  patientId: ObjectId,
  appointmentId: ObjectId,
  issueDate: Date,
  status: String,  // Đã thanh toán, Chưa thanh toán
  items: [
    {
      type: String,  // Dịch vụ, Thuốc
      itemId: ObjectId,
      name: String,
      quantity: Number,
      unitPrice: Number,
      totalPrice: Number
    }
  ],
  subtotal: Number,
  discount: {
    type: String,    // Phần trăm, Số tiền cố định
    value: Number,
    reason: String
  },
  tax: Number,
  grandTotal: Number,
  paymentMethod: String,  // Tiền mặt, Thẻ, Chuyển khoản
  paymentDate: Date,
  issuedBy: ObjectId,  // Người lập hóa đơn
  notes: String,
  createdAt: Date,
  updatedAt: Date
}

COLLECTION: Medical Reports

{
  _id: ObjectId,
  recordId: String,
  patientId: ObjectId,
  visitDate: Date,
  doctorId: ObjectId,
  vitalSigns: {
    temperature: Number,
    bloodPressure: {
      systolic: Number,
      diastolic: Number
    },
    heartRate: Number,
    respiratoryRate: Number
  },
  symptoms: [String],
  diagnosis: [String],
  treatment: {
    medications: [
      {
        medicationId: ObjectId,
        name: String,
        dosage: String,
        frequency: String,
        duration: String,
        instructions: String
      }
    ],
    procedures: [
      {
        serviceId: ObjectId,
        name: String,
        notes: String,
        results: String
      }
    ],
    recommendations: String
  },
  labResults: [
    {
      testName: String,
      testDate: Date,
      result: String,
      normalRange: String,
      interpretation: String
    }
  ],
  notes: String,
  followUp: {
    required: Boolean,
    recommendedDate: Date,
    reason: String
  },
  createdAt: Date,
  updatedAt: Date
}

COLLECTION: Department

{
  _id: ObjectId,
  departmentId: String,
  name: String,
  description: String,
  head: ObjectId,  // Trưởng khoa
  location: String,
  contactNumber: String,
  services: [ObjectId],  // Các dịch vụ thuộc khoa
  status: String,
  createdAt: Date,
  updatedAt: Date
}

COLLECTION: Users

{
  _id: ObjectId,
  username: String,
  passwordHash: String,
  role: String,  // admin, doctor, receptionist
  staffId: ObjectId,  // Tham chiếu đến bác sĩ hoặc tiếp tân
  status: String,  // Hoạt động, Khóa
  lastLogin: Date,
  permissions: [String],
  createdAt: Date,
  updatedAt: Date
}

COLLECTION: Prescriptions

{
  _id: ObjectId,
  prescriptionId: String,
  patientId: ObjectId,
  doctorId: ObjectId,
  issueDate: Date,
  medications: [
    {
      medicationId: ObjectId,
      name: String,
      dosage: String,
      frequency: String,  // VD: "2 lần/ngày"
      duration: String,   // VD: "7 ngày"
      quantity: Number,
      instructions: String
    }
  ],
  notes: String,
  status: String,  // Đã phát, Chưa phát
  dispensedBy: ObjectId,
  dispensedDate: Date,
  createdAt: Date,
  updatedAt: Date
}
