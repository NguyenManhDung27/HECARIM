const mongoose = require('mongoose');

const medicationSchema = new mongoose.Schema({
    medicationId: {
        type: String,
        required: true,
        unique: true
    },
    name: {
        type: String,
        required: true
    },
    genericName: {
        type: String,
        required: true
    },
    category: {
        type: String,
        required: true
    },
    manufacturer: {
        type: String,
        required: true
    },
    description: String,
    dosageForm: {
        type: String,
        required: true,
        enum: ['Viên', 'Siro', 'Ống tiêm', 'Thuốc mỡ', 'Thuốc nhỏ mắt', 'Thuốc nhỏ mũi', 'Khác']
    },
    strength: {
        type: String,
        required: true
    },
    usageInstructions: {
        type: String,
        required: true
    },
    sideEffects: [{
        type: String
    }],
    contraindications: [{
        type: String
    }],
    price: {
        type: Number,
        required: true,
        min: 0
    },
    stock: {
        quantity: {
            type: Number,
            required: true,
            min: 0
        },
        batchNumber: {
            type: String,
            required: true
        },
        expiryDate: {
            type: Date,
            required: true
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
medicationSchema.index({ medicationId: 1 }, { unique: true });
medicationSchema.index({ name: 'text', genericName: 'text' });
medicationSchema.index({ category: 1 });
medicationSchema.index({ manufacturer: 1 });
medicationSchema.index({ 'stock.expiryDate': 1 });
medicationSchema.index({ price: 1 });

// Virtual for checking if medication is in stock
medicationSchema.virtual('inStock').get(function() {
    return this.stock.quantity > 0;
});

// Virtual for checking if medication is expired
medicationSchema.virtual('isExpired').get(function() {
    return new Date() > this.stock.expiryDate;
});

// Methods
medicationSchema.methods.updateStock = async function(quantity) {
    if (this.stock.quantity + quantity < 0) {
        throw new Error('Insufficient stock');
    }
    this.stock.quantity += quantity;
    return await this.save();
};

medicationSchema.methods.isLowStock = function(threshold = 10) {
    return this.stock.quantity <= threshold;
};

// Static method to find medications that will expire soon
medicationSchema.statics.findExpiringMedications = function(daysThreshold = 30) {
    const thresholdDate = new Date();
    thresholdDate.setDate(thresholdDate.getDate() + daysThreshold);
    
    return this.find({
        'stock.expiryDate': {
            $gte: new Date(),
            $lte: thresholdDate
        }
    }).sort({ 'stock.expiryDate': 1 });
};

module.exports = mongoose.model('Medication', medicationSchema);