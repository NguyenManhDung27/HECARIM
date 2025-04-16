const express = require('express');
const router = express.Router();
const Appointment = require('../models/appointment.model');
const { protect, authorize, checkAppointmentAccess, asyncHandler } = require('../middleware/auth.middleware');

// Lấy tất cả lịch hẹn (chỉ cho lễ tân)
router.get('/', protect, authorize('receptionist'), asyncHandler(async (req, res) => {
    const { date, doctorId, status } = req.query;
    const query = {};

    if (date) {
        const startDate = new Date(date);
        startDate.setHours(0, 0, 0, 0);
        const endDate = new Date(startDate);
        endDate.setDate(endDate.getDate() + 1);
        query.date = { $gte: startDate, $lt: endDate };
    }

    if (doctorId) query.doctor = doctorId;
    if (status) query.status = status;

    const appointments = await Appointment.find(query)
        .populate('patient', 'personalInfo')
        .populate('doctor', 'personalInfo')
        .sort({ date: 1, 'timeSlot.start': 1 });

    res.json({
        success: true,
        count: appointments.length,
        data: appointments
    });
}));

// Lấy lịch hẹn của bác sĩ
router.get('/doctor/:doctorId', protect, asyncHandler(async (req, res) => {
    const { startDate, endDate } = req.query;
    const query = { doctor: req.params.doctorId };

    if (startDate && endDate) {
        query.date = {
            $gte: new Date(startDate),
            $lte: new Date(endDate)
        };
    }

    const appointments = await Appointment.find(query)
        .populate('patient', 'personalInfo')
        .sort({ date: 1, 'timeSlot.start': 1 });

    res.json({
        success: true,
        count: appointments.length,
        data: appointments
    });
}));

// Lấy lịch hẹn của bệnh nhân
router.get('/patient/:patientId', protect, asyncHandler(async (req, res) => {
    const { status } = req.query;
    const query = { patient: req.params.patientId };

    if (status) query.status = status;

    const appointments = await Appointment.find(query)
        .populate('doctor', 'personalInfo professionalInfo')
        .sort({ date: -1 });

    res.json({
        success: true,
        count: appointments.length,
        data: appointments
    });
}));

// Tạo lịch hẹn mới
router.post('/', protect, authorize('receptionist', 'patient'), asyncHandler(async (req, res) => {
    const { patient, doctor, date, timeSlot, type, reason, department } = req.body;

    // Kiểm tra xung đột lịch hẹn
    const existingAppointment = await Appointment.findOne({
        doctor,
        date: new Date(date),
        'timeSlot.start': timeSlot.start,
        'timeSlot.end': timeSlot.end,
        status: { $ne: 'cancelled' }
    });

    if (existingAppointment) {
        return res.status(400).json({
            success: false,
            message: 'Khung giờ này đã có lịch hẹn khác'
        });
    }

    // Tạo lịch hẹn mới
    const appointment = await Appointment.create({
        patient,
        doctor,
        date,
        timeSlot,
        type,
        reason,
        department,
        createdBy: req.user.id
    });

    res.status(201).json({
        success: true,
        data: appointment
    });
}));

// Cập nhật trạng thái lịch hẹn
router.patch('/:appointmentId/status', protect, checkAppointmentAccess, asyncHandler(async (req, res) => {
    const { status } = req.body;
    const appointment = req.appointment;

    // Kiểm tra quy tắc cập nhật trạng thái
    if (appointment.status === 'completed' && status !== 'cancelled') {
        return res.status(400).json({
            success: false,
            message: 'Không thể thay đổi trạng thái của lịch hẹn đã hoàn thành'
        });
    }

    if (status === 'cancelled' && !appointment.canCancel()) {
        return res.status(400).json({
            success: false,
            message: 'Không thể hủy lịch hẹn trong vòng 24 giờ trước giờ hẹn'
        });
    }

    appointment.status = status;
    await appointment.save();

    res.json({
        success: true,
        data: appointment
    });
}));

// Cập nhật thông tin lịch hẹn
router.put('/:appointmentId', protect, authorize('receptionist'), checkAppointmentAccess, asyncHandler(async (req, res) => {
    const { date, timeSlot, type, reason, department } = req.body;
    const appointment = req.appointment;

    // Kiểm tra xung đột nếu thay đổi thời gian
    if (date !== appointment.date.toISOString() || 
        timeSlot.start !== appointment.timeSlot.start ||
        timeSlot.end !== appointment.timeSlot.end) {
        
        const existingAppointment = await Appointment.findOne({
            doctor: appointment.doctor,
            date: new Date(date),
            'timeSlot.start': timeSlot.start,
            'timeSlot.end': timeSlot.end,
            status: { $ne: 'cancelled' },
            _id: { $ne: appointment._id }
        });

        if (existingAppointment) {
            return res.status(400).json({
                success: false,
                message: 'Khung giờ này đã có lịch hẹn khác'
            });
        }
    }

    // Cập nhật thông tin
    appointment.date = date;
    appointment.timeSlot = timeSlot;
    appointment.type = type;
    appointment.reason = reason;
    appointment.department = department;

    await appointment.save();

    res.json({
        success: true,
        data: appointment
    });
}));

// Xóa lịch hẹn
router.delete('/:appointmentId', protect, authorize('receptionist'), checkAppointmentAccess, asyncHandler(async (req, res) => {
    const appointment = req.appointment;

    if (appointment.status === 'completed') {
        return res.status(400).json({
            success: false,
            message: 'Không thể xóa lịch hẹn đã hoàn thành'
        });
    }

    await appointment.remove();

    res.json({
        success: true,
        message: 'Đã xóa lịch hẹn'
    });
}));

module.exports = router;