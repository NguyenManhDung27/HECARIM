const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const dotenv = require('dotenv');
const path = require('path');

dotenv.config();

const app = express();

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static files from frontend directory
app.use(express.static(path.join(__dirname, '../front-end')));

// Route để serve trang login
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../front-end/login.html'));
});

// MongoDB Connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/hecarim', {
    useNewUrlParser: true,
    useUnifiedTopology: true
})
.then(() => console.log('Đã kết nối đến MongoDB'))
.catch((err) => console.error('Lỗi kết nối MongoDB:', err));

// Import routes
const authRoutes = require('./routes/auth.routes');
const patientRoutes = require('./routes/patient.routes');
const doctorRoutes = require('./routes/doctor.routes');
const appointmentRoutes = require('./routes/appointment.routes');
const medicalRecordRoutes = require('./routes/medicalRecord.routes');

// Sử dụng routes
app.use('/api/auth', authRoutes);
app.use('/api/patients', patientRoutes);
app.use('/api/doctors', doctorRoutes);
app.use('/api/appointments', appointmentRoutes);
app.use('/api/medical-records', medicalRecordRoutes);

// Serve các routes frontend
app.get('/patients/*', (req, res) => {
    res.sendFile(path.join(__dirname, '../front-end/patients/dashboard.html'));
});

app.get('/doctors/*', (req, res) => {
    res.sendFile(path.join(__dirname, '../front-end/doctors/dashboard.html'));
});

app.get('/receptionists/*', (req, res) => {
    res.sendFile(path.join(__dirname, '../front-end/receptionists/dashboard.html'));
});

// Middleware xử lý lỗi
app.use((err, req, res, next) => {
    console.error('Lỗi:', err.stack);
    res.status(500).json({
        success: false,
        message: 'Lỗi server',
        error: process.env.NODE_ENV === 'development' ? err.message : undefined
    });
});

// Route không tồn tại cho API
app.use('/api/*', (req, res) => {
    res.status(404).json({
        success: false,
        message: 'API endpoint không tồn tại'
    });
});

// Các routes khác sẽ trả về trang login
app.use('*', (req, res) => {
    res.sendFile(path.join(__dirname, '../front-end/login.html'));
});

const PORT = process.env.PORT || 5000;

const server = app.listen(PORT, () => {
    console.log(`Server đang chạy trên port ${PORT}`);
    console.log(`Truy cập: http://localhost:${PORT}`);
});

// Xử lý khi có lỗi không được bắt
process.on('unhandledRejection', (err) => {
    console.error('Lỗi không được xử lý:', err);
    // Đóng server một cách an toàn
    server.close(() => process.exit(1));
});