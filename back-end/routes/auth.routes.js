const express = require('express');
const router = express.Router();
const jwt = require('jsonwebtoken');
const User = require('../models/user.model');

// Middleware để xử lý lỗi async
const asyncHandler = fn => (req, res, next) => {
    Promise.resolve(fn(req, res, next)).catch(next);
};

// Đăng nhập
router.post('/login', asyncHandler(async (req, res) => {
    const { username, password } = req.body;

    // Kiểm tra username và password đã được cung cấp
    if (!username || !password) {
        return res.status(400).json({
            success: false,
            message: 'Vui lòng cung cấp username và password'
        });
    }

    // Tìm user
    const user = await User.findOne({ username });
    if (!user) {
        return res.status(401).json({
            success: false,
            message: 'Username hoặc password không đúng'
        });
    }

    // Kiểm tra password
    const isMatch = await user.comparePassword(password);
    if (!isMatch) {
        return res.status(401).json({
            success: false,
            message: 'Username hoặc password không đúng'
        });
    }

    // Tạo JWT token
    const token = jwt.sign(
        { 
            id: user._id,
            role: user.role,
            profileId: user.profileId
        },
        process.env.JWT_SECRET || 'your-secret-key',
        { expiresIn: '1d' }
    );

    // Lấy thông tin profile tương ứng với role
    let profile;
    if (user.role === 'patient') {
        profile = await require('../models/patient.model').findById(user.profileId);
    } else if (user.role === 'doctor') {
        profile = await require('../models/doctor.model').findById(user.profileId);
    }

    res.json({
        success: true,
        token,
        user: {
            id: user._id,
            username: user.username,
            role: user.role,
            email: user.email,
            profile: profile
        }
    });
}));

// Đăng ký tài khoản mới (chỉ cho bệnh nhân)
router.post('/register', asyncHandler(async (req, res) => {
    const { username, password, email, phoneNumber, personalInfo } = req.body;

    // Kiểm tra user đã tồn tại chưa
    const existingUser = await User.findOne({ 
        $or: [{ username }, { email }] 
    });

    if (existingUser) {
        return res.status(400).json({
            success: false,
            message: 'Username hoặc email đã được sử dụng'
        });
    }

    // Tạo hồ sơ bệnh nhân mới
    const patient = await require('../models/patient.model').create({
        personalInfo,
        status: 'active'
    });

    // Tạo user mới
    const user = await User.create({
        username,
        password,
        email,
        phoneNumber,
        role: 'patient',
        profileId: patient._id
    });

    // Tạo JWT token
    const token = jwt.sign(
        { 
            id: user._id,
            role: user.role,
            profileId: patient._id
        },
        process.env.JWT_SECRET || 'your-secret-key',
        { expiresIn: '1d' }
    );

    res.status(201).json({
        success: true,
        token,
        user: {
            id: user._id,
            username: user.username,
            role: user.role,
            email: user.email,
            profile: patient
        }
    });
}));

// Kiểm tra token hợp lệ
router.get('/verify', asyncHandler(async (req, res) => {
    const token = req.headers.authorization?.split(' ')[1];
    
    if (!token) {
        return res.status(401).json({
            success: false,
            message: 'No token provided'
        });
    }

    try {
        const decoded = jwt.verify(token, process.env.JWT_SECRET || 'your-secret-key');
        const user = await User.findById(decoded.id);
        
        if (!user) {
            throw new Error('User not found');
        }

        // Lấy thông tin profile
        let profile;
        if (user.role === 'patient') {
            profile = await require('../models/patient.model').findById(user.profileId);
        } else if (user.role === 'doctor') {
            profile = await require('../models/doctor.model').findById(user.profileId);
        }

        res.json({
            success: true,
            user: {
                id: user._id,
                username: user.username,
                role: user.role,
                email: user.email,
                profile: profile
            }
        });
    } catch (error) {
        res.status(401).json({
            success: false,
            message: 'Invalid token'
        });
    }
}));

// Đổi mật khẩu
router.post('/change-password', asyncHandler(async (req, res) => {
    const { currentPassword, newPassword } = req.body;
    const userId = req.user.id; // Giả sử có middleware auth đã set user

    const user = await User.findById(userId);
    if (!user) {
        return res.status(404).json({
            success: false,
            message: 'User not found'
        });
    }

    // Kiểm tra mật khẩu hiện tại
    const isMatch = await user.comparePassword(currentPassword);
    if (!isMatch) {
        return res.status(401).json({
            success: false,
            message: 'Mật khẩu hiện tại không đúng'
        });
    }

    // Cập nhật mật khẩu mới
    user.password = newPassword;
    await user.save();

    res.json({
        success: true,
        message: 'Đã cập nhật mật khẩu thành công'
    });
}));

module.exports = router;