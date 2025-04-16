const mongoose = require('mongoose');

const appointmentSchema = new mongoose.Schema({
    appointmentId: {
        type: String,
        required: true,
        unique: true
    },
    patientId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'Patient',
        required: true
    },
    doctorId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'Doctor',
        required: true
    },
    appointmentDate: {
        type: Date,
        required: true
    },
    timeSlot: {
        start: {
            type: Date,
            required: true
        },
        end: {
            type: Date,
            required: true
        }
    },
    status: {
        type: String,
        enum: ['scheduled', 'completed', 'cancelled', 'no-show'],
        default: 'scheduled',
        required: true
    },
    type: {
        type: String,
        enum: ['new', 'follow-up'],
        required: true
    },
    reason: {
        type: String,
        required: true
    },
    symptoms: [{
        type: String
    }],
    notes: String,
    createdBy: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true
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
appointmentSchema.index({ appointmentId: 1 }, { unique: true });
appointmentSchema.index({ patientId: 1 });
appointmentSchema.index({ doctorId: 1 });
appointmentSchema.index({ appointmentDate: 1 });
appointmentSchema.index({ status: 1 });
appointmentSchema.index({ createdBy: 1 });

// Methods
appointmentSchema.methods.canCancel = function() {
    // Cannot cancel if appointment is completed or already cancelled
    if (this.status === 'completed' || this.status === 'cancelled') {
        return false;
    }

    // Check if appointment is within 24 hours
    const now = new Date();
    const appointmentTime = new Date(this.appointmentDate);
    const timeDiff = appointmentTime - now;
    const hoursDiff = timeDiff / (1000 * 60 * 60);

    return hoursDiff >= 24;
};

// Validate timeSlot
appointmentSchema.pre('save', function(next) {
    // Ensure end time is after start time
    if (this.timeSlot.end <= this.timeSlot.start) {
        next(new Error('End time must be after start time'));
    }

    // Set appointment date to the same date as timeSlot start
    const startDate = new Date(this.timeSlot.start);
    this.appointmentDate = new Date(startDate.getFullYear(), startDate.getMonth(), startDate.getDate());

    next();
});

module.exports = mongoose.model('Appointment', appointmentSchema);