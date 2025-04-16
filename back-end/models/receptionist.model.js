const mongoose = require('mongoose');

const receptionistSchema = new mongoose.Schema({
    staffId: {
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
    employmentInfo: {
        joinDate: {
            type: Date,
            required: true
        },
        shift: {
            type: String,
            enum: ['Sáng', 'Chiều', 'Tối'],
            required: true
        },
        status: {
            type: String,
            enum: ['active', 'inactive', 'on_leave'],
            default: 'active'
        }
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
receptionistSchema.index({ staffId: 1 }, { unique: true });
receptionistSchema.index({ 'personalInfo.fullName': 'text' });
receptionistSchema.index({ 'personalInfo.idNumber': 1 }, { unique: true });
receptionistSchema.index({ 'personalInfo.phone': 1 });

// Virtual for full name
receptionistSchema.virtual('fullName').get(function() {
    return this.personalInfo.fullName;
});

// Methods
receptionistSchema.methods.isActive = function() {
    return this.employmentInfo.status === 'active';
};

receptionistSchema.methods.setInactive = function() {
    this.employmentInfo.status = 'inactive';
    return this.save();
};

module.exports = mongoose.model('Receptionist', receptionistSchema);