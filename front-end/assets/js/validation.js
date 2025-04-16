// Validation rules collection
const rules = {
    required: (value) => {
        return value !== null && value !== undefined && value.toString().trim() !== '';
    },
    email: (value) => {
        return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
    },
    phone: (value) => {
        return /^[0-9]{10,11}$/.test(value.replace(/\D/g, ''));
    },
    idNumber: (value) => {
        return /^[0-9]{9,12}$/.test(value);
    },
    password: (value) => {
        return /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$/.test(value);
    },
    date: (value) => {
        const date = new Date(value);
        return date instanceof Date && !isNaN(date);
    },
    futureDate: (value) => {
        const date = new Date(value);
        const today = new Date();
        return date > today;
    },
    pastDate: (value) => {
        const date = new Date(value);
        const today = new Date();
        return date < today;
    },
    minLength: (value, min) => {
        return value.length >= min;
    },
    maxLength: (value, max) => {
        return value.length <= max;
    },
    numeric: (value) => {
        return /^\d+$/.test(value);
    },
    decimal: (value) => {
        return /^\d*\.?\d+$/.test(value);
    }
};

// Error messages
const errorMessages = {
    required: 'Trường này là bắt buộc',
    email: 'Email không hợp lệ',
    phone: 'Số điện thoại không hợp lệ',
    idNumber: 'Số CCCD/CMND không hợp lệ',
    password: 'Mật khẩu phải có ít nhất 8 ký tự, bao gồm chữ và số',
    date: 'Ngày không hợp lệ',
    futureDate: 'Ngày phải là một ngày trong tương lai',
    pastDate: 'Ngày phải là một ngày trong quá khứ',
    minLength: (min) => `Phải có ít nhất ${min} ký tự`,
    maxLength: (max) => `Không được vượt quá ${max} ký tự`,
    numeric: 'Chỉ được nhập số',
    decimal: 'Chỉ được nhập số thập phân'
};

// Form validator
class FormValidator {
    constructor(form, validations) {
        this.form = form;
        this.validations = validations;
        this.errors = new Map();
        
        // Setup realtime validation
        this.setupValidation();
    }

    setupValidation() {
        // Add input event listeners
        Object.keys(this.validations).forEach(fieldName => {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                field.addEventListener('input', () => {
                    this.validateField(fieldName, field.value);
                    this.showFieldError(field, fieldName);
                });

                field.addEventListener('blur', () => {
                    this.validateField(fieldName, field.value);
                    this.showFieldError(field, fieldName);
                });
            }
        });

        // Add form submit handler
        this.form.addEventListener('submit', (e) => {
            if (!this.validateAll()) {
                e.preventDefault();
                this.showAllErrors();
            }
        });
    }

    validateField(fieldName, value) {
        const fieldValidations = this.validations[fieldName];
        const errors = [];

        fieldValidations.forEach(validation => {
            if (typeof validation === 'string') {
                // Simple rule (e.g., 'required', 'email')
                if (!rules[validation](value)) {
                    errors.push(errorMessages[validation]);
                }
            } else if (typeof validation === 'object') {
                // Rule with parameters (e.g., {minLength: 5})
                const ruleName = Object.keys(validation)[0];
                const ruleValue = validation[ruleName];
                
                if (!rules[ruleName](value, ruleValue)) {
                    errors.push(typeof errorMessages[ruleName] === 'function' 
                        ? errorMessages[ruleName](ruleValue)
                        : errorMessages[ruleName]);
                }
            }
        });

        if (errors.length > 0) {
            this.errors.set(fieldName, errors);
        } else {
            this.errors.delete(fieldName);
        }

        return errors.length === 0;
    }

    validateAll() {
        let isValid = true;

        Object.keys(this.validations).forEach(fieldName => {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                if (!this.validateField(fieldName, field.value)) {
                    isValid = false;
                }
            }
        });

        return isValid;
    }

    showFieldError(field, fieldName) {
        // Remove existing error message
        const existingError = field.parentElement.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }

        // Show new error if exists
        if (this.errors.has(fieldName)) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.style.color = '#f44336';
            errorDiv.style.fontSize = '12px';
            errorDiv.style.marginTop = '4px';
            errorDiv.textContent = this.errors.get(fieldName)[0];
            field.parentElement.appendChild(errorDiv);
            field.classList.add('error');
        } else {
            field.classList.remove('error');
        }
    }

    showAllErrors() {
        Object.keys(this.validations).forEach(fieldName => {
            const field = this.form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                this.showFieldError(field, fieldName);
            }
        });
    }

    getErrors() {
        return this.errors;
    }

    hasErrors() {
        return this.errors.size > 0;
    }
}

// Example validation configurations
const validationConfigs = {
    patientForm: {
        'personalInfo.fullName': ['required', { minLength: 2 }, { maxLength: 100 }],
        'personalInfo.idNumber': ['required', 'idNumber'],
        'personalInfo.phone': ['required', 'phone'],
        'personalInfo.email': ['email'],
        'personalInfo.dateOfBirth': ['required', 'pastDate'],
        'emergencyContact.name': ['required'],
        'emergencyContact.phone': ['required', 'phone']
    },
    appointmentForm: {
        'patientId': ['required'],
        'doctorId': ['required'],
        'appointmentDate': ['required', 'futureDate'],
        'timeSlot': ['required'],
        'reason': ['required', { minLength: 10 }]
    },
    prescriptionForm: {
        'medication_name[]': ['required'],
        'medication_dosage[]': ['required'],
        'medication_quantity[]': ['required', 'numeric'],
        'medication_instructions[]': ['required']
    },
    medicalRecordForm: {
        'symptoms': ['required'],
        'diagnosis': ['required'],
        'treatment.recommendations': ['required']
    }
};

// Export for use in other files
window.FormValidator = FormValidator;
window.validationConfigs = validationConfigs;