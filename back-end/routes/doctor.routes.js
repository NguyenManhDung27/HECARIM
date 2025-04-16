const express = require('express');
const router = express.Router();
const Doctor = require('../models/doctor.model');
const { protect, authorize, asyncHandler } = require('../middleware/auth.middleware');

// Lấy danh sách bác sĩ
router.get('/', asyncHandler(async (req, res) => {
    const { department, specialization, status } = req.query;
    const query = {};

    if (department) query.department = department;
    if (specialization) query['professionalInfo.specialization'] = specialization;
    if (status) query.status = status;

    const doctors = await Doctor.find(query)
        .select('personalInfo professionalInfo department status');

    res.json({
        success: true,
        count: doctors.length,
        data: doctors
    });
}));

// Lấy thông tin chi tiết một bác sĩ
router.get('/:doctorId', asyncHandler(async (req, res) => {
    const doctor = await Doctor.findById(req.params.doctorId)
        .populate('appointments')
        .populate('patients', 'personalInfo');

    if (!doctor) {
        return res.status(404).json({
            success: false,
            message: 'Không tìm thấy bác sĩ'
        });
    }

    res.json({
        success: true,
        data: doctor
    });
}));

// Tạo bác sĩ mới (chỉ admin)
router.post('/', protect, authorize('admin'), asyncHandler(async (req, res) => {
    const doctor = await Doctor.create(req.body);

    res.status(201).json({
        success: true,
        data: doctor
    });
}));

// Cập nhật thông tin bác sĩ
router.put('/:doctorId', protect, authorize('doctor', 'admin'), asyncHandler(async (req, res) => {
    // Chỉ cho phép bác sĩ cập nhật thông tin của chính mình
    if (req.user.role === 'doctor' && req.user.profileId.toString() !== req.params.doctorId) {
        return res.status(403).json({
            success: false,
            message: 'Không có quyền cập nhật thông tin của bác sĩ khác'
        });
    }

    const doctor = await Doctor.findByIdAndUpdate(
        req.params.doctorId,
        req.body,
        { new: true, runValidators: true }
    );

    if (!doctor) {
        return res.status(404).json({
            success: false,
            message: 'Không tìm thấy bác sĩ'
        });
    }

    res.json({
        success: true,
        data: doctor
    });
}));

// Cập nhật lịch làm việc
router.put('/:doctorId/schedule', protect, authorize('doctor', 'admin'), asyncHandler(async (req, res) => {
    const { regularHours, exceptions } = req.body;
    const doctor = await Doctor.findById(req.params.doctorId);

    if (!doctor) {
        return res.status(404).json({
            success: false,
            message: 'Không tìm thấy bác sĩ'
        });
    }

    if (regularHours) doctor.schedule.regularHours = regularHours;
    if (exceptions) doctor.schedule.exceptions = exceptions;

    await doctor.save();

    res.json({
        success: true,
        data: doctor
    });
}));

// Lấy lịch làm việc của bác sĩ
router.get('/:doctorId/schedule', asyncHandler(async (req, res) => {
    const { date } = req.query;
    const doctor = await Doctor.findById(req.params.doctorId)
        .select('schedule personalInfo.fullName');

    if (!doctor) {
        return res.status(404).json({
            success: false,
            message: 'Không tìm thấy bác sĩ'
        });
    }

    // Nếu có ngày cụ thể, kiểm tra xem có lịch ngoại lệ không
    if (date) {
        const exception = doctor.schedule.exceptions.find(
            e => e.date.toISOString().split('T')[0] === date
        );
        if (exception) {
            return res.json({
                success: true,
                data: {
                    isException: true,
                    ...exception.toObject()
                }
            });
        }
    }

    res.json({
        success: true,
        data: doctor.schedule
    });
}));

// Cập nhật trạng thái bác sĩ
router.patch('/:doctorId/status', protect, authorize('admin'), asyncHandler(async (req, res) => {
    const { status } = req.body;
    const doctor = await Doctor.findByIdAndUpdate(
        req.params.doctorId,
        { status },
        { new: true }
    );

    if (!doctor) {
        return res.status(404).json({
            success: false,
            message: 'Không tìm thấy bác sĩ'
        });
    }

    res.json({
        success: true,
        data: doctor
    });
}));

// Lấy thống kê của bác sĩ
router.get('/:doctorId/statistics', protect, authorize('doctor', 'admin'), asyncHandler(async (req, res) => {
    const doctor = await Doctor.findById(req.params.doctorId);
    
    if (!doctor) {
        return res.status(404).json({
            success: false,
            message: 'Không tìm thấy bác sĩ'
        });
    }

    await doctor.updateStatistics();

    res.json({
        success: true,
        data: doctor.statistics
    });
}));

module.exports = router;