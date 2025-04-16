const mongoose = require('mongoose');

const invoiceSchema = new mongoose.Schema({
    invoiceId: {
        type: String,
        required: true,
        unique: true
    },
    patientId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'Patient',
        required: true
    },
    appointmentId: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'Appointment',
        required: true
    },
    issueDate: {
        type: Date,
        required: true,
        default: Date.now
    },
    status: {
        type: String,
        enum: ['pending', 'paid', 'cancelled', 'refunded'],
        default: 'pending'
    },
    items: [{
        type: {
            type: String,
            enum: ['Dịch vụ', 'Thuốc'],
            required: true
        },
        itemId: {
            type: mongoose.Schema.Types.ObjectId,
            refPath: 'items.type',
            required: true
        },
        name: {
            type: String,
            required: true
        },
        quantity: {
            type: Number,
            required: true,
            min: 1
        },
        unitPrice: {
            type: Number,
            required: true,
            min: 0
        },
        totalPrice: {
            type: Number,
            required: true,
            min: 0
        }
    }],
    subtotal: {
        type: Number,
        required: true,
        min: 0
    },
    discount: {
        type: {
            type: String,
            enum: ['percentage', 'fixed'],
            required: function() {
                return this.discount.value > 0;
            }
        },
        value: {
            type: Number,
            default: 0,
            min: 0
        },
        reason: String
    },
    tax: {
        type: Number,
        required: true,
        min: 0
    },
    grandTotal: {
        type: Number,
        required: true,
        min: 0
    },
    paymentMethod: {
        type: String,
        enum: ['cash', 'card', 'transfer', 'insurance'],
        required: function() {
            return this.status === 'paid';
        }
    },
    paymentDate: {
        type: Date,
        required: function() {
            return this.status === 'paid';
        }
    },
    issuedBy: {
        type: mongoose.Schema.Types.ObjectId,
        ref: 'User',
        required: true
    },
    notes: String,
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
invoiceSchema.index({ invoiceId: 1 }, { unique: true });
invoiceSchema.index({ patientId: 1 });
invoiceSchema.index({ appointmentId: 1 });
invoiceSchema.index({ status: 1 });
invoiceSchema.index({ issueDate: 1 });
invoiceSchema.index({ issuedBy: 1 });

// Virtual for formatted amounts
invoiceSchema.virtual('formattedGrandTotal').get(function() {
    return new Intl.NumberFormat('vi-VN', {
        style: 'currency',
        currency: 'VND'
    }).format(this.grandTotal);
});

// Methods
invoiceSchema.methods.calculateTotals = function() {
    // Calculate subtotal
    this.subtotal = this.items.reduce((sum, item) => sum + item.totalPrice, 0);

    // Calculate discount amount
    let discountAmount = 0;
    if (this.discount.value > 0) {
        if (this.discount.type === 'percentage') {
            discountAmount = this.subtotal * (this.discount.value / 100);
        } else {
            discountAmount = this.discount.value;
        }
    }

    // Calculate tax
    this.tax = (this.subtotal - discountAmount) * 0.1; // 10% VAT

    // Calculate grand total
    this.grandTotal = this.subtotal - discountAmount + this.tax;

    return this;
};

invoiceSchema.methods.markAsPaid = async function(paymentMethod) {
    this.status = 'paid';
    this.paymentMethod = paymentMethod;
    this.paymentDate = new Date();
    return await this.save();
};

invoiceSchema.methods.refund = async function(reason) {
    if (this.status !== 'paid') {
        throw new Error('Only paid invoices can be refunded');
    }
    this.status = 'refunded';
    this.notes = this.notes ? `${this.notes}\nRefund reason: ${reason}` : `Refund reason: ${reason}`;
    return await this.save();
};

// Middleware to calculate totals before saving
invoiceSchema.pre('save', function(next) {
    if (this.isModified('items') || this.isModified('discount')) {
        this.calculateTotals();
    }
    next();
});

module.exports = mongoose.model('Invoice', invoiceSchema);