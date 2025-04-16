const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({
    username: {
        type: String,
        required: true,
        unique: true,
        trim: true,
        minlength: 3
    },
    passwordHash: {
        type: String,
        required: true
    },
    role: {
        type: String,
        enum: ['admin', 'doctor', 'receptionist'],
        required: true
    },
    staffId: {
        type: mongoose.Schema.Types.ObjectId,
        refPath: 'role',
        required: true
    },
    status: {
        type: String,
        enum: ['active', 'inactive', 'locked'],
        default: 'active'
    },
    lastLogin: {
        type: Date
    },
    permissions: [{
        type: String,
        enum: [
            'view_patients',
            'edit_patients',
            'view_appointments',
            'edit_appointments',
            'view_medical_records',
            'edit_medical_records',
            'view_prescriptions',
            'edit_prescriptions',
            'view_invoices',
            'edit_invoices',
            'view_reports',
            'manage_users',
            'manage_departments'
        ]
    }],
    passwordResetToken: String,
    passwordResetExpires: Date,
    loginAttempts: {
        type: Number,
        default: 0
    },
    lockUntil: Date,
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
userSchema.index({ username: 1 }, { unique: true });
userSchema.index({ role: 1 });
userSchema.index({ status: 1 });
userSchema.index({ staffId: 1 });

// Virtual to check if account is locked
userSchema.virtual('isLocked').get(function() {
    return !!(this.lockUntil && this.lockUntil > Date.now());
});

// Methods
userSchema.methods.incrementLoginAttempts = async function() {
    // If account is already locked, do nothing
    if (this.isLocked) return;

    // Increment attempts
    this.loginAttempts += 1;

    // Lock account if too many attempts
    if (this.loginAttempts >= 5) {
        this.lockUntil = Date.now() + 3600000; // Lock for 1 hour
    }

    await this.save();
};

userSchema.methods.resetLoginAttempts = async function() {
    this.loginAttempts = 0;
    this.lockUntil = undefined;
    await this.save();
};

userSchema.methods.updateLastLogin = async function() {
    this.lastLogin = new Date();
    await this.save();
};

userSchema.methods.hasPermission = function(permission) {
    return this.permissions.includes(permission);
};

// Set default permissions based on role
userSchema.pre('save', function(next) {
    if (this.isNew || this.isModified('role')) {
        switch (this.role) {
            case 'admin':
                this.permissions = [
                    'view_patients', 'edit_patients',
                    'view_appointments', 'edit_appointments',
                    'view_medical_records', 'edit_medical_records',
                    'view_prescriptions', 'edit_prescriptions',
                    'view_invoices', 'edit_invoices',
                    'view_reports', 'manage_users',
                    'manage_departments'
                ];
                break;
            case 'doctor':
                this.permissions = [
                    'view_patients', 'edit_medical_records',
                    'view_appointments', 'view_medical_records',
                    'edit_prescriptions', 'view_prescriptions'
                ];
                break;
            case 'receptionist':
                this.permissions = [
                    'view_patients', 'edit_patients',
                    'view_appointments', 'edit_appointments',
                    'view_invoices', 'edit_invoices'
                ];
                break;
        }
    }
    next();
});

module.exports = mongoose.model('User', userSchema);