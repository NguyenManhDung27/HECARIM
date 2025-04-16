// API utilities for making requests
const Api = {
    // Base URL for API requests
    baseUrl: '/api',

    // Default headers
    headers: {
        'Content-Type': 'application/json'
    },

    // Initialize API with authentication token
    init() {
        const token = localStorage.getItem('token');
        if (token) {
            this.headers['Authorization'] = `Bearer ${token}`;
        }
    },

    // Set authentication token
    setToken(token) {
        localStorage.setItem('token', token);
        this.headers['Authorization'] = `Bearer ${token}`;
    },

    // Clear authentication token
    clearToken() {
        localStorage.removeItem('token');
        delete this.headers['Authorization'];
    },

    // Generic request method
    async request(endpoint, options = {}) {
        try {
            const url = `${this.baseUrl}${endpoint}`;
            const response = await fetch(url, {
                ...options,
                headers: {
                    ...this.headers,
                    ...options.headers
                }
            });

            const data = await response.json();

            if (!response.ok) {
                throw {
                    status: response.status,
                    data: data
                };
            }

            return data;
        } catch (error) {
            throw this.handleError(error);
        }
    },

    // GET request
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    },

    // POST request
    async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    // PUT request
    async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    },

    // PATCH request
    async patch(endpoint, data) {
        return this.request(endpoint, {
            method: 'PATCH',
            body: JSON.stringify(data)
        });
    },

    // DELETE request
    async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    },

    // Upload files
    async upload(endpoint, files, data = {}) {
        const formData = new FormData();
        
        // Append files
        if (Array.isArray(files)) {
            files.forEach(file => formData.append('files', file));
        } else {
            formData.append('file', files);
        }

        // Append additional data
        Object.keys(data).forEach(key => {
            formData.append(key, data[key]);
        });

        return this.request(endpoint, {
            method: 'POST',
            headers: {
                // Remove Content-Type to let browser set it with boundary
                'Authorization': this.headers['Authorization']
            },
            body: formData
        });
    },

    // API Endpoints
    endpoints: {
        auth: {
            login: '/auth/login',
            logout: '/auth/logout',
            refresh: '/auth/refresh'
        },
        patients: {
            list: '/patients',
            create: '/patients',
            get: (id) => `/patients/${id}`,
            update: (id) => `/patients/${id}`,
            delete: (id) => `/patients/${id}`,
            search: '/patients/search'
        },
        appointments: {
            list: '/appointments',
            create: '/appointments',
            get: (id) => `/appointments/${id}`,
            update: (id) => `/appointments/${id}`,
            delete: (id) => `/appointments/${id}`,
            updateStatus: (id) => `/appointments/${id}/status`,
            checkConflict: '/appointments/check-conflict'
        },
        medicalRecords: {
            list: '/medical-records',
            create: '/medical-records',
            get: (id) => `/medical-records/${id}`,
            update: (id) => `/medical-records/${id}`,
            delete: (id) => `/medical-records/${id}`,
            addTestResult: (id) => `/medical-records/${id}/test-results`,
            addPrescription: (id) => `/medical-records/${id}/prescriptions`,
            updateStatus: (id) => `/medical-records/${id}/status`,
            uploadAttachment: (id) => `/medical-records/${id}/attachments`,
            deleteAttachment: (id, attachmentId) => `/medical-records/${id}/attachments/${attachmentId}`
        },
        doctors: {
            list: '/doctors',
            get: (id) => `/doctors/${id}`,
            getSchedule: (id) => `/doctors/${id}/schedule`,
            updateSchedule: (id) => `/doctors/${id}/schedule`,
            status: '/doctors/status'
        }
    },

    // Error handling
    handleError(error) {
        if (error.status === 401) {
            // Unauthorized - clear token and redirect to login
            this.clearToken();
            window.location.href = '/login.html';
            return;
        }

        if (error.data) {
            return {
                status: error.status,
                message: error.data.message || 'Có lỗi xảy ra',
                errors: error.data.errors
            };
        }

        return {
            status: 500,
            message: 'Không thể kết nối đến máy chủ'
        };
    }
};

// Initialize API
Api.init();

// Export for use in other files
window.Api = Api;