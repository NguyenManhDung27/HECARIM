const mongoose = require('mongoose');

const prescriptionSchema = new mongoose.Schema({
    prescriptionId: {
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
    issueDate: {
        type: Date,
        required: true,
        default: Date.now
    },
    medications: [{
        medicationId: {
            type: mongoose.Schema.Types.ObjectId,
            ref: 'Medication',
            required: true
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
        quantity: {
            type: Number,
            required: true,
            min: 1
        },
        instructions: String
    }],
    notes: String,
    status: {
        type: String,
        enum: ['active', 'completed', 'cancelled'],
        default: 'active'
    },
    dispensedBy: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User'
    },
    dispensedDate: Date,
    validUntil: {
        type: Date,
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
prescriptionSchema.index({ prescriptionId: 1 }, { unique: true });
prescriptionSchema.index({ patientId: 1 });
prescriptionSchema.index({ doctorId: 1 });
prescriptionSchema.index({ status: 1 });
prescriptionSchema.index({ issueDate: 1 });
prescriptionSchema.index({ validUntil: 1 });

// Virtual for checking if prescription is expired
prescriptionSchema.virtual('isExpired').get(function() {
    return new Date() > this.validUntil;
});

// Virtual for checking if prescription is dispensed
prescriptionSchema.virtual('isDispensed').get(function() {
    return !!this.dispensedDate;
});

// Methods
prescriptionSchema.methods.dispense = async function(userId) {
    if (this.isExpired) {
        throw new Error('Cannot dispense expired prescription');
    }
    if (this.isDispensed) {
        throw new Error('Prescription has already been dispensed');
    }
    if (this.status !== 'active') {
        throw new Error('Can only dispense active prescriptions');
    }

    this.dispensedBy = userId;
    this.dispensedDate = new Date();
    this.status = 'completed';
    await this.save();
};

prescriptionSchema.methods.cancel = async function(reason) {
    if (this.isDispensed) {
        throw new Error('Cannot cancel dispensed prescription');
    }

    this.status = 'cancelled';
    this.notes = this.notes ? `${this.notes}\nCancellation reason: ${reason}` : `Cancellation reason: ${reason}`;
    await this.save();
};

// Pre-save middleware to set validUntil date if not set
prescriptionSchema.pre('save', function(next) {
    if (!this.validUntil) {
        // Default validity is 7 days from issue
        this.validUntil = new Date(this.issueDate.getTime() + (7 * 24 * 60 * 60 * 1000));
    }
    next();
});

// Static method to find active prescriptions for a patient
prescriptionSchema.statics.findActiveForPatient = function(patientId) {
    return this.find({
        patientId: patientId,
        status: 'active',
        validUntil: { $gt: new Date() }
    }).sort({ issueDate: -1 });
};

module.exports = mongoose.model('Prescription', prescriptionSchema);