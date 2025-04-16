const mongoose = require('mongoose');

const medicalRecordSchema = new mongoose.Schema({
    recordId: {
        type: String,
        required: true,
        unique: true
    },
    patientId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'Patient',
        required: true
    },
    visitDate: {
        type: Date,
        required: true
    },
    doctorId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'Doctor',
        required: true
    },
    vitalSigns: {
        temperature: {
            type: Number,
            required: true
        },
        bloodPressure: {
            systolic: {
                type: Number,
                required: true
            },
            diastolic: {
                type: Number,
                required: true
            }
        },
        heartRate: {
            type: Number,
            required: true
        },
        respiratoryRate: {
            type: Number,
            required: true
        }
    },
    symptoms: [{
        type: String,
        required: true
    }],
    diagnosis: [{
        type: String,
        required: true
    }],
    treatment: {
        medications: [{
            medicationId: {
                type: mongoose.Schema.Types.ObjectId,
                ref: 'Medication'
            },
            name: {
                type: String,
                required: true
            },
            dosage: {
                type: String,
                required: true
            },
            frequency: {
                type: String,
                required: true
            },
            duration: {
                type: String,
                required: true
            },
            instructions: String
        }],
        procedures: [{
            serviceId: {
                type: mongoose.Schema.Types.ObjectId,
                ref: 'Service'
            },
            name: {
                type: String,
                required: true
            },
            notes: String,
            results: String
        }],
        recommendations: String
    },
    labResults: [{
        testName: {
            type: String,
            required: true
        },
        testDate: {
            type: Date,
            required: true
        },
        result: {
            type: String,
            required: true
        },
        normalRange: String,
        interpretation: String
    }],
    notes: String,
    followUp: {
        required: {
            type: Boolean,
            default: false
        },
        recommendedDate: Date,
        reason: String
    },
    attachments: [{
        fileName: String,
        fileType: String,
        fileUrl: String,
        uploadedAt: Date
    }],
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
medicalRecordSchema.index({ recordId: 1 }, { unique: true });
medicalRecordSchema.index({ patientId: 1 });
medicalRecordSchema.index({ doctorId: 1 });
medicalRecordSchema.index({ visitDate: 1 });
medicalRecordSchema.index({ 'diagnosis': 'text' });

// Virtual for patient age at time of visit
medicalRecordSchema.virtual('patientAgeAtVisit').get(function() {
    return this.patient ? Math.floor((this.visitDate - this.patient.personalInfo.dateOfBirth) / 31557600000) : null;
});

// Methods for tracking record status
medicalRecordSchema.methods.isComplete = function() {
    return this.diagnosis && this.diagnosis.length > 0 && this.treatment;
};

medicalRecordSchema.methods.requiresFollowUp = function() {
    return this.followUp && this.followUp.required;
};

module.exports = mongoose.model('MedicalRecord', medicalRecordSchema);