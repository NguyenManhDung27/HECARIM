const express = require('express');
const router = express.Router();
const Patient = require('../models/patient.model');
const { protect, authorize, checkPatientAccess, asyncHandler } = require('../middleware/auth.middleware');

// Lấy danh sách bệnh nhân (chỉ cho bác sĩ và lễ tân)
router.get('/', protect, authorize('doctor', 'receptionist'), asyncHandler(async (req, res) => {
    const { search, status } = req.query;
    const query = {};

    if (status) query.status = status;
    if (search) {
        query['personalInfo.fullName'] = { $regex: search, $options: 'i' };
    }

    const patients = await Patient.find(query)
        .populate('assignedDoctor', 'personalInfo.fullName')
        .select('-medicalRecords');

    res.json({
        success: true,
        count: patients.length,
        data: patients
    });
}));

// Lấy thông tin một bệnh nhân
router.get('/:patientId', protect, checkPatientAccess, asyncHandler(async (req, res) => {
    const patient = await Patient.findById(req.params.patientId)
        .populate('assignedDoctor', 'personalInfo.fullName professionalInfo.specialization')
        .populate('appointments');

    if (!patient) {
        return res.status(404).json({
            success: false,
            message: 'Không tìm thấy bệnh nhân'
        });
    }

    res.json({
        success: true,
        data: patient
    });
}));

// Tạo bệnh nhân mới (chỉ cho lễ tân)
router.post('/', protect, authorize('receptionist'), asyncHandler(async (req, res) => {
    const patient = await Patient.create(req.body);

    res.status(201).json({
        success: true,
        data: patient
    });
}));

// Cập nhật thông tin bệnh nhân
router.put('/:patientId', protect, checkPatientAccess, asyncHandler(async (req, res) => {
    const patient = await Patient.findByIdAndUpdate(
        req.params.patientId,
        req.body,
        { new: true, runValidators: true }
    );

    if (!patient) {
        return res.status(404).json({
            success: false,
            message: 'Không tìm thấy bệnh nhân'
        });
    }

    res.json({
        success: true,
        data: patient
    });
}));

// Cập nhật trạng thái bệnh nhân (chỉ cho lễ tân và bác sĩ)
router.patch('/:patientId/status', protect, authorize('doctor', 'receptionist'), asyncHandler(async (req, res) => {
    const { status } = req.body;
    const patient = await Patient.findByIdAndUpdate(
        req.params.patientId,
        { status },
        { new: true }
    );

    if (!patient) {
        return res.status(404).json({
            success: false,
            message: 'Không tìm thấy bệnh nhân'
        });
    }

    res.json({
        success: true,
        data: patient
    });
}));

// Phân công bác sĩ cho bệnh nhân (chỉ cho lễ tân)
router.patch('/:patientId/assign-doctor', protect, authorize('receptionist'), asyncHandler(async (req, res) => {
    const { doctorId } = req.body;
    const patient = await Patient.findByIdAndUpdate(
        req.params.patientId,
        { assignedDoctor: doctorId },
        { new: true }
    ).populate('assignedDoctor', 'personalInfo.fullName');

    if (!patient) {
        return res.status(404).json({
            success: false,
            message: 'Không tìm thấy bệnh nhân'
        });
    }

    res.json({
        success: true,
        data: patient
    });
}));

module.exports = router;