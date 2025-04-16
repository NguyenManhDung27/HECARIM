const express = require('express');
const router = express.Router();
const MedicalRecord = require('../models/medicalRecord.model');
const { protect, authorize, checkPatientAccess, asyncHandler } = require('../middleware/auth.middleware');
const { upload, processUploadedFiles, deleteFile } = require('../utils/fileUpload');

// Lấy tất cả hồ sơ của một bệnh nhân
router.get('/patient/:patientId', protect, checkPatientAccess, asyncHandler(async (req, res) => {
    const records = await MedicalRecord.find({ patient: req.params.patientId })
        .populate('doctor', 'personalInfo.fullName professionalInfo.specialization')
        .sort({ date: -1 });

    res.json({
        success: true,
        count: records.length,
        data: records
    });
}));

// Lấy chi tiết một hồ sơ
router.get('/:recordId', protect, asyncHandler(async (req, res) => {
    const record = await MedicalRecord.findById(req.params.recordId)
        .populate('doctor', 'personalInfo.fullName professionalInfo.specialization')
        .populate('patient', 'personalInfo');

    if (!record) {
        return res.status(404).json({
            success: false,
            message: 'Không tìm thấy hồ sơ'
        });
    }

    // Kiểm tra quyền truy cập
    if (req.user.role === 'patient' && 
        record.patient._id.toString() !== req.user.profileId.toString()) {
        return res.status(403).json({
            success: false,
            message: 'Không có quyền truy cập hồ sơ này'
        });
    }

    res.json({
        success: true,
        data: record
    });
}));

// Tạo hồ sơ mới
router.post('/', protect, authorize('doctor'), asyncHandler(async (req, res) => {
    const {
        patient,
        appointment,
        visitType,
        chiefComplaint,
        symptoms,
        diagnosis,
        vitals,
        examinations,
        prescriptions,
        treatment,
        notes
    } = req.body;

    const record = await MedicalRecord.create({
        patient,
        doctor: req.user.profileId,
        appointment,
        visitType,
        chiefComplaint,
        symptoms,
        diagnosis,
        vitals,
        examinations,
        prescriptions,
        treatment,
        notes,
        status: 'draft'
    });

    res.status(201).json({
        success: true,
        data: record
    });
}));

// Cập nhật hồ sơ
router.put('/:recordId', protect, authorize('doctor'), asyncHandler(async (req, res) => {
    const record = await MedicalRecord.findById(req.params.recordId);

    if (!record) {
        return res.status(404).json({
            success: false,
            message: 'Không tìm thấy hồ sơ'
        });
    }

    // Chỉ cho phép bác sĩ tạo hồ sơ được cập nhật
    if (record.doctor.toString() !== req.user.profileId.toString()) {
        return res.status(403).json({
            success: false,
            message: 'Không có quyền cập nhật hồ sơ này'
        });
    }

    // Không cho phép cập nhật hồ sơ đã hoàn thành
    if (record.status === 'final' && req.body.status !== 'amended') {
        return res.status(400).json({
            success: false,
            message: 'Không thể cập nhật hồ sơ đã hoàn thành'
        });
    }

    // Cập nhật thông tin
    Object.keys(req.body).forEach(key => {
        record[key] = req.body[key];
    });

    await record.save();

    res.json({
        success: true,
        data: record
    });
}));

// Thêm kết quả xét nghiệm với tập tin đính kèm
router.post('/:recordId/test-results', 
    protect, 
    authorize('doctor'), 
    upload.array('files', 5),
    asyncHandler(async (req, res) => {
        const record = await MedicalRecord.findById(req.params.recordId);

        if (!record) {
            return res.status(404).json({
                success: false,
                message: 'Không tìm thấy hồ sơ'
            });
        }

        const testResult = {
            ...req.body,
            files: req.files ? processUploadedFiles(req.files) : []
        };

        record.testResults.push(testResult);
        await record.save();

        res.status(201).json({
            success: true,
            data: record
        });
    }
));

// Thêm đơn thuốc
router.post('/:recordId/prescriptions', protect, authorize('doctor'), asyncHandler(async (req, res) => {
    const record = await MedicalRecord.findById(req.params.recordId);

    if (!record) {
        return res.status(404).json({
            success: false,
            message: 'Không tìm thấy hồ sơ'
        });
    }

    record.prescriptions.push(req.body);
    await record.save();

    res.status(201).json({
        success: true,
        data: record
    });
}));

// Cập nhật trạng thái hồ sơ
router.patch('/:recordId/status', protect, authorize('doctor'), asyncHandler(async (req, res) => {
    const { status } = req.body;
    const record = await MedicalRecord.findById(req.params.recordId);

    if (!record) {
        return res.status(404).json({
            success: false,
            message: 'Không tìm thấy hồ sơ'
        });
    }

    // Kiểm tra quyền cập nhật
    if (record.doctor.toString() !== req.user.profileId.toString()) {
        return res.status(403).json({
            success: false,
            message: 'Không có quyền cập nhật hồ sơ này'
        });
    }

    record.status = status;
    await record.save();

    res.json({
        success: true,
        data: record
    });
}));

// Tải lên tài liệu đính kèm
router.post('/:recordId/attachments', 
    protect, 
    authorize('doctor'), 
    upload.array('files', 5),
    asyncHandler(async (req, res) => {
        const record = await MedicalRecord.findById(req.params.recordId);

        if (!record) {
            return res.status(404).json({
                success: false,
                message: 'Không tìm thấy hồ sơ'
            });
        }

        // Xử lý các file đã tải lên
        const attachments = processUploadedFiles(req.files);

        // Thêm các attachment mới vào record
        record.attachments.push(...attachments);
        await record.save();

        res.status(201).json({
            success: true,
            data: record
        });
    }
));

// Xóa tài liệu đính kèm
router.delete('/:recordId/attachments/:attachmentId', 
    protect, 
    authorize('doctor'), 
    asyncHandler(async (req, res) => {
        const record = await MedicalRecord.findById(req.params.recordId);

        if (!record) {
            return res.status(404).json({
                success: false,
                message: 'Không tìm thấy hồ sơ'
            });
        }

        // Tìm attachment cần xóa
        const attachment = record.attachments.id(req.params.attachmentId);
        if (!attachment) {
            return res.status(404).json({
                success: false,
                message: 'Không tìm thấy tập tin đính kèm'
            });
        }

        // Xóa file từ storage
        deleteFile(attachment.path);

        // Xóa attachment từ record
        attachment.remove();
        await record.save();

        res.json({
            success: true,
            message: 'Đã xóa tập tin đính kèm'
        });
    }
));

module.exports = router;