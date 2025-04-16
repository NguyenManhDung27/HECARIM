const jwt = require('jsonwebtoken');
const User = require('../models/user.model');

// Xác thực token JWT
exports.protect = async (req, res, next) => {
    try {
        let token;

        // Lấy token từ header Authorization
        if (req.headers.authorization && req.headers.authorization.startsWith('Bearer')) {
            token = req.headers.authorization.split(' ')[1];
        }

        if (!token) {
            return res.status(401).json({
                success: false,
                message: 'Không có quyền truy cập. Vui lòng đăng nhập.'
            });
        }

        try {
            // Verify token
            const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key');

            // Lấy thông tin user và attach vào request
            const user = await User.findById(decoded.id);
            if (!user) {
                throw new Error('User không tồn tại');
            }

            req.user = {
                id: user._id,
                role: user.role,
                profileId: user.profileId
            };

            next();
        } catch (error) {
            return res.status(401).json({
                success: false,
                message: 'Token không hợp lệ hoặc đã hết hạn'
            });
        }
    } catch (error) {
        next(error);
    }
};

// Kiểm tra role
exports.authorize = (...roles) => {
    return (req, res, next) => {
        if (!roles.includes(req.user.role)) {
            return res.status(403).json({
                success: false,
                message: 'Không có quyền thực hiện thao tác này'
            });
        }
        next();
    };
};

// Middleware kiểm tra quyền truy cập hồ sơ bệnh nhân
exports.checkPatientAccess = async (req, res, next) => {
    try {
        const patientId = req.params.patientId || req.body.patientId;
        
        // Nếu là bệnh nhân, chỉ được xem hồ sơ của chính mình
        if (req.user.role === 'patient' && req.user.profileId.toString() !== patientId) {
            return res.status(403).json({
                success: false,
                message: 'Không có quyền truy cập hồ sơ này'
            });
        }

        // Nếu là bác sĩ, kiểm tra xem bệnh nhân có phải của mình không
        if (req.user.role === 'doctor') {
            const patient = await require('../models/patient.model').findById(patientId);
            if (!patient || patient.assignedDoctor.toString() !== req.user.profileId.toString()) {
                return res.status(403).json({
                    success: false,
                    message: 'Không có quyền truy cập hồ sơ này'
                });
            }
        }

        next();
    } catch (error) {
        next(error);
    }
};

// Middleware kiểm tra quyền truy cập lịch hẹn
exports.checkAppointmentAccess = async (req, res, next) => {
    try {
        const appointmentId = req.params.appointmentId || req.body.appointmentId;
        const appointment = await require('../models/appointment.model').findById(appointmentId);

        if (!appointment) {
            return res.status(404).json({
                success: false,
                message: 'Không tìm thấy lịch hẹn'
            });
        }

        // Kiểm tra quyền truy cập dựa trên role
        if (req.user.role === 'patient' && 
            appointment.patient.toString() !== req.user.profileId.toString()) {
            return res.status(403).json({
                success: false,
                message: 'Không có quyền truy cập lịch hẹn này'
            });
        }

        if (req.user.role === 'doctor' && 
            appointment.doctor.toString() !== req.user.profileId.toString()) {
            return res.status(403).json({
                success: false,
                message: 'Không có quyền truy cập lịch hẹn này'
            });
        }

        req.appointment = appointment;
        next();
    } catch (error) {
        next(error);
    }
};

// Middleware xử lý lỗi async
exports.asyncHandler = fn => (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
};