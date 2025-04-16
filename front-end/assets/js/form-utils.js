// Form utilities for common operations
const FormUtils = {
    // Initialize form with data
    initForm(form, data, prefix = '') {
        Object.keys(data).forEach(key => {
            const value = data[key];
            if (value !== null && typeof value === 'object' && !Array.isArray(value)) {
                // Handle nested objects
                this.initForm(form, value, `${prefix}${key}.`);
            } else {
                const field = form.querySelector(`[name="${prefix}${key}"]`);
                if (field) {
                    if (field.type === 'checkbox') {
                        field.checked = value;
                    } else if (field.type === 'date') {
                        // Format date for input
                        field.value = value ? new Date(value).toISOString().split('T')[0] : '';
                    } else {
                        field.value = value || '';
                    }

                    // Trigger change event for dynamic updates
                    field.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
        });
    },

    // Collect form data including nested objects
    collectFormData(form) {
        const formData = new FormData(form);
        const data = {};

        formData.forEach((value, key) => {
            if (key.includes('.')) {
                // Handle nested fields (e.g., "personalInfo.fullName")
                const keys = key.split('.');
                let current = data;
                
                keys.forEach((k, i) => {
                    if (i === keys.length - 1) {
                        current[k] = value;
                    } else {
                        current[k] = current[k] || {};
                        current = current[k];
                    }
                });
            } else {
                data[key] = value;
            }
        });

        return data;
    },

    // Handle array inputs (e.g., multiple medications)
    collectArrayInputs(form, prefix) {
        const items = [];
        const inputs = form.querySelectorAll(`[name^="${prefix}"]`);
        const size = inputs.length / 4; // Assuming 4 fields per item

        for (let i = 0; i < size; i++) {
            const item = {};
            inputs.forEach(input => {
                const name = input.getAttribute('name').replace('[]', '');
                if (input.dataset.index === i.toString()) {
                    item[name] = input.value;
                }
            });
            if (Object.keys(item).length > 0) {
                items.push(item);
            }
        }

        return items;
    },

    // Add dynamic form fields
    addDynamicField(container, template, index) {
        const newField = template.replace(/\[INDEX\]/g, index);
        container.insertAdjacentHTML('beforeend', newField);
    },

    // Remove dynamic field
    removeDynamicField(button) {
        button.closest('.dynamic-field').remove();
    },

    // Reset form to initial state
    resetForm(form) {
        form.reset();
        const dynamicContainers = form.querySelectorAll('.dynamic-container');
        dynamicContainers.forEach(container => {
            container.innerHTML = '';
        });
    },

    // Show loading state
    showLoading(form) {
        const submitBtn = form.querySelector('[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.dataset.originalText = submitBtn.textContent;
            submitBtn.textContent = 'Đang xử lý...';
        }
        form.classList.add('loading');
    },

    // Hide loading state
    hideLoading(form) {
        const submitBtn = form.querySelector('[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = submitBtn.dataset.originalText;
        }
        form.classList.remove('loading');
    },

    // Handle API errors
    handleApiError(error, form) {
        this.hideLoading(form);
        
        if (error.response) {
            // Server response with error status
            const data = error.response.data;
            if (data.errors) {
                // Show validation errors
                Object.keys(data.errors).forEach(field => {
                    const input = form.querySelector(`[name="${field}"]`);
                    if (input) {
                        this.showFieldError(input, data.errors[field]);
                    }
                });
            } else {
                // Show general error
                this.showFormError(form, data.message || 'Có lỗi xảy ra, vui lòng thử lại');
            }
        } else if (error.request) {
            // No response received
            this.showFormError(form, 'Không thể kết nối đến máy chủ');
        } else {
            // Request setup error
            this.showFormError(form, 'Có lỗi xảy ra, vui lòng thử lại');
        }
    },

    // Show field-specific error
    showFieldError(input, message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'field-error';
        errorDiv.textContent = message;
        
        // Remove existing error
        const existingError = input.parentElement.querySelector('.field-error');
        if (existingError) {
            existingError.remove();
        }
        
        input.parentElement.appendChild(errorDiv);
        input.classList.add('error');
    },

    // Show form-level error
    showFormError(form, message) {
        let errorContainer = form.querySelector('.form-error');
        if (!errorContainer) {
            errorContainer = document.createElement('div');
            errorContainer.className = 'form-error';
            form.insertBefore(errorContainer, form.firstChild);
        }
        errorContainer.textContent = message;
        errorContainer.style.display = 'block';
    },

    // Clear all errors
    clearErrors(form) {
        const errors = form.querySelectorAll('.field-error, .form-error');
        errors.forEach(error => error.remove());
        
        const errorInputs = form.querySelectorAll('.error');
        errorInputs.forEach(input => input.classList.remove('error'));
    }
};

// Export for use in other files
window.FormUtils = FormUtils;