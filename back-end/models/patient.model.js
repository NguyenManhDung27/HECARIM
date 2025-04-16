const mongoose = require('mongoose');

const patientSchema = new mongoose.Schema({
    patientId: {
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
        email: String,
        emergencyContact: {
            name: {
                type: String,
                required: true
            },
            relationship: {
                type: String,
                required: true
            },
            phone: {
                type: String,
                required: true
            }
        }
    },
    healthInfo: {
        bloodType: {
            type: String,
            enum: ['A+', 'A-', 'B+', 'B-', 'O+', 'O-', 'AB+', 'AB-']
        },
        allergies: [String],
        chronicDiseases: [String],
        familyMedicalHistory: String,
        height: Number,
        weight: Number
    },
    medicalHistory: [{
        diagnosisDate: Date,
        symptoms: [String],
        diagnosis: String,
        treatment: String,
        doctor: {
            type: mongoose.Schema.Types.ObjectId,
            ref: 'Doctor'
        },
        notes: String
    }],
    insurance: {
        provider: String,
        policyNumber: String,
        expiryDate: Date
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
patientSchema.index({ patientId: 1 }, { unique: true });
patientSchema.index({ 'personalInfo.fullName': 'text' });
patientSchema.index({ 'personalInfo.idNumber': 1 }, { unique: true });
patientSchema.index({ 'personalInfo.phone': 1 });
patientSchema.index({ 'personalInfo.email': 1 });

module.exports = mongoose.model('Patient', patientSchema);