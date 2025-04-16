let currentPatient = null;
let currentMedicalRecord = null;
let medications = [];
let testResults = [];

// Initialize page
document.addEventListener('DOMContentLoaded', async () => {
    // Get patient ID and record ID from URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const patientId = urlParams.get('patientId');
    const recordId = urlParams.get('recordId');

    if (patientId) {
        await loadPatientInfo(patientId);
        await loadPatientHistory(patientId);
    }

    if (recordId) {
        await loadMedicalRecord(recordId);
    }

    // Setup event listeners
    setupFormListeners();
    setupFileUpload();
});

// Load patient information
async function loadPatientInfo(patientId) {
    try {
        const response = await fetch(`/api/patients/${patientId}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });

        if (!response.ok) throw new Error('Failed to load patient information');
        
        currentPatient = await response.json();
        updatePatientInfoDisplay();
    } catch (error) {
        console.error('Error loading patient info:', error);
        showError('Không thể tải thông tin bệnh nhân');
    }
}

// Load medical record
async function loadMedicalRecord(recordId) {
    try {
        const response = await fetch(`/api/medical-records/${recordId}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });

        if (!response.ok) throw new Error('Failed to load medical record');
        
        currentMedicalRecord = await response.json();
        populateForm(currentMedicalRecord);
    } catch (error) {
        console.error('Error loading medical record:', error);
        showError('Không thể tải hồ sơ khám bệnh');
    }
}

// Load patient history
async function loadPatientHistory(patientId) {
    try {
        const response = await fetch(`/api/medical-records/patient/${patientId}`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });

        if (!response.ok) throw new Error('Failed to load patient history');
        
        const history = await response.json();
        updateHistoryDisplay(history);
    } catch (error) {
        console.error('Error loading patient history:', error);
        showError('Không thể tải lịch sử khám bệnh');
    }
}

// Save medical record
async function saveMedicalRecord(formData) {
    try {
        const url = currentMedicalRecord?._id 
            ? `/api/medical-records/${currentMedicalRecord._id}`
            : '/api/medical-records';
        
        const method = currentMedicalRecord?._id ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(formData)
        });

        if (!response.ok) throw new Error('Failed to save medical record');
        
        const savedRecord = await response.json();
        showSuccess('Đã lưu hồ sơ khám bệnh thành công');
        
        if (!currentMedicalRecord?._id) {
            // Redirect to edit page if this was a new record
            window.location.href = `edit-record.html?recordId=${savedRecord._id}`;
        }
    } catch (error) {
        console.error('Error saving medical record:', error);
        showError('Không thể lưu hồ sơ khám bệnh');
    }
}

// Add prescription item
function addPrescriptionItem() {
    const container = document.querySelector('#prescriptionItems');
    const itemHtml = `
        <div class="prescription-item">
            <div class="form-group" style="flex: 2;">
                <label>Tên thuốc:</label>
                <input type="text" name="medication_name[]" required>
            </div>
            <div class="form-group">
                <label>Liều lượng:</label>
                <input type="text" name="medication_dosage[]" required>
            </div>
            <div class="form-group">
                <label>Số lượng:</label>
                <input type="number" name="medication_quantity[]" required>
            </div>
            <div class="form-group">
                <label>Cách dùng:</label>
                <input type="text" name="medication_instructions[]" required>
            </div>
            <button type="button" onclick="removePrescriptionItem(this)" style="margin-top: 20px;">Xóa</button>
        </div>
    `;
    container.insertAdjacentHTML('beforeend', itemHtml);
}

// Remove prescription item
function removePrescriptionItem(button) {
    button.closest('.prescription-item').remove();
}

// Handle file upload
async function handleFileUpload(files) {
    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }

    try {
        const response = await fetch('/api/medical-records/upload', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: formData
        });

        if (!response.ok) throw new Error('Failed to upload files');
        
        const result = await response.json();
        updateFileList(result.files);
        showSuccess('Đã tải lên tập tin thành công');
    } catch (error) {
        console.error('Error uploading files:', error);
        showError('Không thể tải lên tập tin');
    }
}

// Update patient info display
function updatePatientInfoDisplay() {
    document.getElementById('patientId').value = currentPatient.patientId;
    document.getElementById('patientName').value = currentPatient.personalInfo.fullName;
    document.getElementById('patientDob').value = new Date(currentPatient.personalInfo.dateOfBirth)
        .toLocaleDateString('vi-VN');
}

// Update history display
function updateHistoryDisplay(history) {
    const container = document.getElementById('medicalHistory');
    container.innerHTML = history.map(record => `
        <div class="history-item">
            <div style="display: flex; justify-content: space-between;">
                <strong>Ngày: ${new Date(record.visitDate).toLocaleDateString('vi-VN')}</strong>
                <span>BS. ${record.doctorName}</span>
            </div>
            <p><strong>Chẩn đoán:</strong> ${record.diagnosis.join(', ')}</p>
            <p><strong>Đơn thuốc:</strong> ${record.treatment.medications.map(m => m.name).join(', ')}</p>
            <button type="button" class="btn-small" onclick="viewRecordDetail('${record._id}')">
                Xem Chi Tiết
            </button>
        </div>
    `).join('');
}

// View record detail
function viewRecordDetail(recordId) {
    window.location.href = `edit-record.html?recordId=${recordId}`;
}

// Setup form listeners
function setupFormListeners() {
    const form = document.querySelector('form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(form);
        
        // Collect form data
        const medicalRecord = {
            patientId: currentPatient._id,
            visitDate: formData.get('visitDate'),
            symptoms: formData.get('symptoms').split('\n'),
            diagnosis: formData.get('diagnosis').split('\n'),
            treatment: {
                medications: collectPrescriptions(),
                procedures: collectProcedures(),
                recommendations: formData.get('recommendations')
            },
            followUp: {
                required: formData.get('followUpRequired') === 'true',
                recommendedDate: formData.get('followUpDate'),
                reason: formData.get('followUpNotes')
            },
            notes: formData.get('notes')
        };

        await saveMedicalRecord(medicalRecord);
    });

    // Add prescription button
    document.querySelector('.btn-add-prescription').addEventListener('click', addPrescriptionItem);
}

// Setup file upload
function setupFileUpload() {
    const dropZone = document.querySelector('.file-upload');
    const fileInput = dropZone.querySelector('input[type="file"]');

    dropZone.addEventListener('click', () => fileInput.click());
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        handleFileUpload(e.dataTransfer.files);
    });
    fileInput.addEventListener('change', (e) => {
        handleFileUpload(e.target.files);
    });
}

// Helper functions
function collectPrescriptions() {
    const medications = [];
    const names = document.getElementsByName('medication_name[]');
    const dosages = document.getElementsByName('medication_dosage[]');
    const quantities = document.getElementsByName('medication_quantity[]');
    const instructions = document.getElementsByName('medication_instructions[]');

    for (let i = 0; i < names.length; i++) {
        medications.push({
            name: names[i].value,
            dosage: dosages[i].value,
            quantity: parseInt(quantities[i].value),
            instructions: instructions[i].value
        });
    }

    return medications;
}

function collectProcedures() {
    const procedures = [];
    const types = document.getElementsByName('test_type[]');
    const notes = document.getElementsByName('test_notes[]');

    for (let i = 0; i < types.length; i++) {
        procedures.push({
            name: types[i].value,
            notes: notes[i].value
        });
    }

    return procedures;
}

function showError(message) {
    alert(message);
}

function showSuccess(message) {
    alert(message);
}