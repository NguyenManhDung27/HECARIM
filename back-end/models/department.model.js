const mongoose = require('mongoose');

const departmentSchema = new mongoose.Schema({
    departmentId: {
        type: String,
        required: true,
        unique: true
    },
    name: {
        type: String,
        required: true,
        unique: true
    },
    description: {
        type: String,
        required: true
    },
    head: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'Doctor',
        required: true
    },
    location: {
        type: String,
        required: true
    },
    contactNumber: {
        type: String,
        required: true
    },
    services: [{
        type: mongoose.Schema.Types.ObjectId,
        ref: 'Service'
    }],
    status: {
        type: String,
        enum: ['active', 'inactive', 'maintenance'],
        default: 'active'
    },
    operatingHours: {
        weekdays: {
            open: {
                type: String,
                default: '08:00'
            },
            close: {
                type: String,
                default: '17:00'
            }
        },
        weekend: {
            open: {
                type: String,
                default: '08:00'
            },
            close: {
                type: String,
                default: '12:00'
            }
        }
    },
    capacity: {
        maxPatients: {
            type: Number,
            required: true
        },
        maxDoctors: {
            type: Number,
            required: true
        }
    },
    staff: {
        doctors: [{
            type: mongoose.Schema.Types.ObjectId,
            ref: 'Doctor'
        }],
        nurses: [{
            type: mongoose.Schema.Types.ObjectId,
            ref: 'Staff'
        }]
    },
    equipment: [{
        name: String,
        quantity: Number,
        status: {
            type: String,
            enum: ['available', 'in_use', 'maintenance', 'out_of_order'],
            default: 'available'
        }
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
departmentSchema.index({ departmentId: 1 }, { unique: true });
departmentSchema.index({ name: 'text' });
departmentSchema.index({ status: 1 });
departmentSchema.index({ head: 1 });

// Virtual for checking if department is at capacity
departmentSchema.virtual('isAtCapacity').get(function() {
    return this.staff.doctors.length >= this.capacity.maxDoctors;
});

// Methods
departmentSchema.methods.addDoctor = async function(doctorId) {
    if (this.isAtCapacity) {
        throw new Error('Department is at maximum capacity for doctors');
    }
    if (!this.staff.doctors.includes(doctorId)) {
        this.staff.doctors.push(doctorId);
        await this.save();
    }
};

departmentSchema.methods.removeDoctor = async function(doctorId) {
    this.staff.doctors = this.staff.doctors.filter(id => id.toString() !== doctorId.toString());
    await this.save();
};

departmentSchema.methods.addService = async function(serviceId) {
    if (!this.services.includes(serviceId)) {
        this.services.push(serviceId);
        await this.save();
    }
};

departmentSchema.methods.updateEquipment = async function(equipmentName, quantity, status) {
    const equipment = this.equipment.find(e => e.name === equipmentName);
    if (equipment) {
        equipment.quantity = quantity;
        equipment.status = status;
    } else {
        this.equipment.push({ name: equipmentName, quantity, status });
    }
    await this.save();
};

module.exports = mongoose.model('Department', departmentSchema);