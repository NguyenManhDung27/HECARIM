const mongoose = require('mongoose');

const doctorSchema = new mongoose.Schema({
    doctorId: {
        type: String,
        required: true,
        unique: true
    },
    personalInfo: {
        fullName: {
            type: String,
            required: true
        },
        gender: {
            type: String,
            enum: ['male', 'female', 'other'],
            required: true
        },
        dateOfBirth: {
            type: Date,
            required: true
        },
        idNumber: {
            type: String,
            required: true,
            unique: true
        },
        address: {
            type: String,
            required: true
        },
        phone: {
            type: String,
            required: true
        },
        email: String
    },
    professionalInfo: {
        specialization: {
            type: String,
            required: true
        },
        qualification: [{
            type: String,
            required: true
        }],
        licenseNumber: {
            type: String,
            required: true,
            unique: true
        },
        experience: {
            type: Number,
            required: true
        },
        department: {
            type: String,
            required: true
        }
    },
    schedule: {
        workDays: [{
            type: String,
            enum: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        }],
        workHours: {
            start: {
                type: String,
                required: true
            },
            end: {
                type: String,
                required: true
            }
        },
        vacationDates: [Date]
    },
    createdAt: {
        type: Date,
        default: Date.now
    },
    updatedAt: {
        type: Date,
        default: Date.now
    }
}, {
    timestamps: true
});

// Indexes
doctorSchema.index({ doctorId: 1 }, { unique: true });
doctorSchema.index({ 'personalInfo.fullName': 'text' });
doctorSchema.index({ 'personalInfo.idNumber': 1 }, { unique: true });
doctorSchema.index({ 'professionalInfo.licenseNumber': 1 }, { unique: true });
doctorSchema.index({ 'professionalInfo.specialization': 1 });
doctorSchema.index({ 'professionalInfo.department': 1 });

module.exports = mongoose.model('Doctor', doctorSchema);