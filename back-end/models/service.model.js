const mongoose = require('mongoose');

const serviceSchema = new mongoose.Schema({
    serviceId: {
        type: String,
        required: true,
        unique: true
    },
    name: {
        type: String,
        required: true
    },
    category: {
        type: String,
        required: true,
        enum: [
            'Khám tổng quát',
            'Nội soi',
            'Xét nghiệm',
            'Chụp X-quang',
            'Siêu âm',
            'Điện tim',
            'Vật lý trị liệu',
            'Khác'
        ]
    },
    description: {
        type: String,
        required: true
    },
    duration: {
        type: Number,
        required: true,
        min: 5,
        max: 480 // 8 hours in minutes
    },
    price: {
        type: Number,
        required: true,
        min: 0
    },
    requiredEquipment: [{
        type: String
    }],
    preparationInstructions: {
        type: String
    },
    department: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'Department',
        required: true
    },
    status: {
        type: String,
        enum: ['active', 'inactive', 'maintenance'],
        default: 'active'
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
serviceSchema.index({ serviceId: 1 }, { unique: true });
serviceSchema.index({ name: 'text' });
serviceSchema.index({ category: 1 });
serviceSchema.index({ department: 1 });
serviceSchema.index({ status: 1 });
serviceSchema.index({ price: 1 });

// Virtual for formatted duration
serviceSchema.virtual('formattedDuration').get(function() {
    const hours = Math.floor(this.duration / 60);
    const minutes = this.duration % 60;
    if (hours > 0) {
        return `${hours} giờ ${minutes > 0 ? minutes + ' phút' : ''}`;
    }
    return `${minutes} phút`;
});

// Virtual for formatted price
serviceSchema.virtual('formattedPrice').get(function() {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND'
    }).format(this.price);
});

// Methods
serviceSchema.methods.isAvailable = function() {
    return this.status === 'active';
};

serviceSchema.methods.setStatus = async function(status) {
    this.status = status;
    return await this.save();
};

// Static method to find services by department
serviceSchema.statics.findByDepartment = function(departmentId) {
    return this.find({
        department: departmentId,
        status: 'active'
    }).sort({ name: 1 });
};

// Static method to find services by price range
serviceSchema.statics.findByPriceRange = function(minPrice, maxPrice) {
    return this.find({
        price: {
            $gte: minPrice,
            $lte: maxPrice
        },
        status: 'active'
    }).sort({ price: 1 });
};

// Static method to find services by duration
serviceSchema.statics.findByDuration = function(maxDuration) {
    return this.find({
        duration: { $lte: maxDuration },
        status: 'active'
    }).sort({ duration: 1 });
};

module.exports = mongoose.model('Service', serviceSchema);