// Lưu trữ trạng thái lịch và bác sĩ
let selectedDoctor = null;
let selectedDate = null;
let appointments = [];
let doctors = [];

// Khởi tạo trang
document.addEventListener('DOMContentLoaded', async () => {
    // Set ngày mặc định là hôm nay
    const today = new Date().toISOString().split('T')[0];
    document.querySelector('input[type="date"]').value = today;
    selectedDate = today;

    // Load dữ liệu ban đầu
    await Promise.all([
        loadDoctors(),
        loadAppointments(today)
    ]);

    // Thêm event listeners
    setupEventListeners();
});

// Load danh sách bác sĩ
async function loadDoctors() {
    try {
        const response = await fetch('/api/doctors', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        if (!response.ok) throw new Error('Không thể tải danh sách bác sĩ');
        
        doctors = await response.json();
        updateDoctorSelect(doctors);
    } catch (error) {
        console.error('Lỗi khi tải danh sách bác sĩ:', error);
        showError('Không thể tải danh sách bác sĩ');
    }
}

// Load lịch hẹn theo ngày
async function loadAppointments(date) {
    try {
        const response = await fetch(`/api/appointments?date=${date}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        if (!response.ok) throw new Error('Không thể tải lịch hẹn');
        
        appointments = await response.json();
        updateScheduleDisplay();
    } catch (error) {
        console.error('Lỗi khi tải lịch hẹn:', error);
        showError('Không thể tải lịch hẹn');
    }
}

// Tìm kiếm bệnh nhân
async function searchPatient(query) {
    try {
        const response = await fetch(`/api/patients/search?q=${encodeURIComponent(query)}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        if (!response.ok) throw new Error('Không thể tìm kiếm bệnh nhân');
        
        const patients = await response.json();
        updatePatientSearchResults(patients);
    } catch (error) {
        console.error('Lỗi khi tìm kiếm bệnh nhân:', error);
        showError('Không thể tìm kiếm bệnh nhân');
    }
}

// Kiểm tra xung đột lịch hẹn
async function checkScheduleConflict(doctorId, date, timeSlot) {
    try {
        const response = await fetch('/api/appointments/check-conflict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify({ doctorId, date, timeSlot })
        });
        
        const result = await response.json();
        return result.hasConflict;
    } catch (error) {
        console.error('Lỗi khi kiểm tra xung đột:', error);
        throw new Error('Không thể kiểm tra xung đột lịch hẹn');
    }
}

// Tạo lịch hẹn mới
async function createAppointment(appointmentData) {
    try {
        const response = await fetch('/api/appointments', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(appointmentData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.message || 'Không thể tạo lịch hẹn');
        }

        const result = await response.json();
        showSuccess('Đã tạo lịch hẹn thành công');
        await loadAppointments(selectedDate);
    } catch (error) {
        console.error('Lỗi khi tạo lịch hẹn:', error);
        showError(error.message);
    }
}

// Cập nhật trạng thái lịch hẹn
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

        if (!response.ok) throw new Error('Không thể cập nhật trạng thái');

        await loadAppointments(selectedDate);
        showSuccess('Đã cập nhật trạng thái lịch hẹn');
    } catch (error) {
        console.error('Lỗi khi cập nhật trạng thái:', error);
        showError('Không thể cập nhật trạng thái lịch hẹn');
    }
}

// Cập nhật giao diện
function updateDoctorSelect(doctors) {
    const select = document.querySelector('select[name="doctor"]');
    select.innerHTML = '<option value="">Chọn bác sĩ</option>';
    doctors.forEach(doctor => {
        select.innerHTML += `
            <option value="${doctor._id}">
                BS. ${doctor.personalInfo.fullName} - ${doctor.professionalInfo.specialization}
            </option>
        `;
    });
}

function updateScheduleDisplay() {
    const container = document.querySelector('.schedule-container');
    const scheduleSection = container.querySelector('.doctor-schedules');
    scheduleSection.innerHTML = '';

    // Nhóm lịch hẹn theo bác sĩ
    const appointmentsByDoctor = appointments.reduce((acc, appointment) => {
        if (!acc[appointment.doctorId]) acc[appointment.doctorId] = [];
        acc[appointment.doctorId].push(appointment);
        return acc;
    }, {});

    doctors.forEach(doctor => {
        const doctorSchedule = createDoctorScheduleElement(doctor, appointmentsByDoctor[doctor._id] || []);
        scheduleSection.appendChild(doctorSchedule);
    });
}

function createDoctorScheduleElement(doctor, doctorAppointments) {
    const div = document.createElement('div');
    div.className = 'doctor-schedule';
    
    // Tạo các khung giờ từ 8:00 đến 17:00
    const timeSlots = generateTimeSlots();
    
    div.innerHTML = `
        <h4>BS. ${doctor.personalInfo.fullName} - ${doctor.professionalInfo.specialization}</h4>
        ${timeSlots.map(slot => {
            const appointment = doctorAppointments.find(a => 
                a.timeSlot.start === slot.start && a.timeSlot.end === slot.end
            );
            
            return createTimeSlotElement(slot, appointment);
        }).join('')}
    `;

    return div;
}

function createTimeSlotElement(slot, appointment) {
    let statusClass = 'status-available';
    let statusText = 'Còn trống';
    let patientInfo = '';

    if (appointment) {
        statusClass = `status-${appointment.status}`;
        statusText = getStatusText(appointment.status);
        patientInfo = `<span>${appointment.patientName}</span>`;
    }

    return `
        <div class="time-slot">
            <div>
                <strong>${slot.start} - ${slot.end}</strong>
                ${patientInfo}
            </div>
            <span class="status-tag ${statusClass}">${statusText}</span>
        </div>
    `;
}

// Các hàm tiện ích
function generateTimeSlots() {
    const slots = [];
    const startHour = 8;
    const endHour = 17;
    
    for (let hour = startHour; hour < endHour; hour++) {
        for (let minute = 0; minute < 60; minute += 30) {
            const start = `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`;
            const endMinute = (minute + 30) % 60;
            const endHour = minute + 30 >= 60 ? hour + 1 : hour;
            const end = `${endHour.toString().padStart(2, '0')}:${endMinute.toString().padStart(2, '0')}`;
            
            slots.push({ start, end });
        }
    }
    
    return slots;
}

function getStatusText(status) {
    const statusMap = {
        'scheduled': 'Đã đặt lịch',
        'completed': 'Đã khám',
        'cancelled': 'Đã hủy',
        'no-show': 'Không đến'
    };
    return statusMap[status] || status;
}

function showError(message) {
    // Hiển thị thông báo lỗi
    alert(message);
}

function showSuccess(message) {
    // Hiển thị thông báo thành công
    alert(message);
}

// Thiết lập các event listeners
function setupEventListeners() {
    // Xử lý thay đổi ngày
    document.querySelector('input[type="date"]').addEventListener('change', (e) => {
        selectedDate = e.target.value;
        loadAppointments(selectedDate);
    });

    // Xử lý thay đổi bác sĩ
    document.querySelector('select[name="doctor"]').addEventListener('change', (e) => {
        selectedDoctor = e.target.value;
    });

    // Xử lý tìm kiếm bệnh nhân
    const searchInput = document.querySelector('input[placeholder="Nhập tên hoặc mã bệnh nhân..."]');
    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            if (e.target.value.length >= 2) {
                searchPatient(e.target.value);
            }
        }, 300);
    });

    // Xử lý form đặt lịch
    document.querySelector('form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        
        try {
            // Kiểm tra xung đột
            const hasConflict = await checkScheduleConflict(
                formData.get('doctor'),
                formData.get('date'),
                formData.get('timeSlot')
            );

            if (hasConflict) {
                showError('Khung giờ này đã có lịch hẹn khác');
                return;
            }

            // Tạo lịch hẹn
            await createAppointment(Object.fromEntries(formData));
            e.target.reset();
            
        } catch (error) {
            showError(error.message);
        }
    });
}