// Dashboard state
let currentStats = {
    todayAppointments: 0,
    waitingPatients: 0,
    newPatients: 0,
    totalMonthlyAppointments: 0,
    activeDoctors: 0
};

let activeDoctors = [];
let todayAppointments = [];

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
    await Promise.all([
        loadDashboardStats(),
        loadTodayAppointments(),
        loadDoctorStatus(),
        loadNotifications()
    ]);

    // Refresh data every 5 minutes
    setInterval(refreshDashboard, 300000);
});

// Load dashboard statistics
async function loadDashboardStats() {
    try {
        const response = await fetch('/api/appointments/stats', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) throw new Error('Failed to load statistics');
        
        const stats = await response.json();
        updateDashboardStats(stats);
    } catch (error) {
        console.error('Error loading dashboard stats:', error);
        showError('Không thể tải thông tin thống kê');
    }
}

// Load today's appointments
async function loadTodayAppointments() {
    try {
        const today = new Date().toISOString().split('T')[0];
        const response = await fetch(`/api/appointments?date=${today}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) throw new Error('Failed to load appointments');
        
        todayAppointments = await response.json();
        updateAppointmentsList(todayAppointments);
    } catch (error) {
        console.error('Error loading appointments:', error);
        showError('Không thể tải danh sách lịch hẹn');
    }
}

// Load doctor status
async function loadDoctorStatus() {
    try {
        const response = await fetch('/api/doctors/status', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) throw new Error('Failed to load doctor status');
        
        activeDoctors = await response.json();
        updateDoctorStatus(activeDoctors);
    } catch (error) {
        console.error('Error loading doctor status:', error);
        showError('Không thể tải trạng thái bác sĩ');
    }
}

// Load notifications
async function loadNotifications() {
    try {
        const response = await fetch('/api/notifications/receptionist', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (!response.ok) throw new Error('Failed to load notifications');
        
        const notifications = await response.json();
        updateNotifications(notifications);
    } catch (error) {
        console.error('Error loading notifications:', error);
        showError('Không thể tải thông báo');
    }
}

// Update appointment status
async function updateAppointmentStatus(appointmentId, status) {
    try {
        const response = await fetch(`/api/appointments/${appointmentId}/status`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ status })
        });

        if (!response.ok) throw new Error('Failed to update appointment status');

        // Refresh appointments list
        await loadTodayAppointments();
        showSuccess('Đã cập nhật trạng thái lịch hẹn');
    } catch (error) {
        console.error('Error updating appointment status:', error);
        showError('Không thể cập nhật trạng thái lịch hẹn');
    }
}

// UI Update Functions
function updateDashboardStats(stats) {
    document.getElementById('todayAppointments').textContent = stats.todayAppointments;
    document.getElementById('waitingPatients').textContent = stats.waitingPatients;
    document.getElementById('newPatients').textContent = stats.newPatients;
    document.getElementById('monthlyAppointments').textContent = stats.totalMonthlyAppointments;
    document.getElementById('activeDoctors').textContent = stats.activeDoctors;
}

function updateAppointmentsList(appointments) {
    const container = document.getElementById('appointmentsList');
    container.innerHTML = '';

    appointments.forEach(appointment => {
        const timeSlot = document.createElement('div');
        timeSlot.className = 'time-slot';
        timeSlot.innerHTML = `
            <div>
                <strong>${formatTime(appointment.timeSlot.start)}</strong> - 
                ${appointment.patientName}
                <span style="color: #666;">(BS. ${appointment.doctorName})</span>
            </div>
            <div class="action-buttons">
                ${getActionButtons(appointment)}
            </div>
        `;
        container.appendChild(timeSlot);
    });
}

function updateDoctorStatus(doctors) {
    const container = document.getElementById('doctorStatus');
    container.innerHTML = '';

    doctors.forEach(doctor => {
        const statusDiv = document.createElement('div');
        statusDiv.className = 'doctor-status';
        statusDiv.innerHTML = `
            <span class="status-indicator ${doctor.status}"></span>
            <span>BS. ${doctor.personalInfo.fullName}</span>
            <span style="margin-left: auto;">${getDoctorStatusText(doctor.status)}</span>
        `;
        container.appendChild(statusDiv);
    });
}

function updateNotifications(notifications) {
    const container = document.getElementById('notifications');
    container.innerHTML = '';

    notifications.forEach(notification => {
        const notifDiv = document.createElement('div');
        notifDiv.className = `notification ${notification.type}`;
        notifDiv.innerHTML = `
            <strong>${notification.title}</strong>
            <p>${notification.message}</p>
        `;
        container.appendChild(notifDiv);
    });
}

// Helper Functions
function formatTime(timeString) {
    return new Date(timeString).toLocaleTimeString('vi-VN', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getDoctorStatusText(status) {
    const statusMap = {
        'available': 'Đang làm việc',
        'busy': 'Đang khám',
        'away': 'Nghỉ',
        'off': 'Nghỉ phép'
    };
    return statusMap[status] || status;
}

function getActionButtons(appointment) {
    const buttons = [];
    
    switch(appointment.status) {
        case 'scheduled':
            buttons.push(`
                <button onclick="updateAppointmentStatus('${appointment._id}', 'completed')" 
                        class="btn-small">Check-in</button>
                <button onclick="updateAppointmentStatus('${appointment._id}', 'cancelled')" 
                        class="btn-small">Hủy</button>
            `);
            break;
        case 'in_progress':
            buttons.push(`
                <button onclick="updateAppointmentStatus('${appointment._id}', 'completed')" 
                        class="btn-small">Hoàn thành</button>
            `);
            break;
    }

    return buttons.join('');
}

function showError(message) {
    // Implement error notification
    alert(message);
}

function showSuccess(message) {
    // Implement success notification
    alert(message);
}

// Refresh dashboard data
async function refreshDashboard() {
    await Promise.all([
        loadDashboardStats(),
        loadTodayAppointments(),
        loadDoctorStatus()
    ]);
}