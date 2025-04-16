const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');
const User = require('../models/user.model');
const Doctor = require('../models/doctor.model');
const Patient = require('../models/patient.model');
const { hashPassword } = require('../utils/auth');

let mongoServer;

// Connect to in-memory database before all tests
beforeAll(async () => {
    mongoServer = await MongoMemoryServer.create();
    const mongoUri = mongoServer.getUri();
    await mongoose.connect(mongoUri);
});

// Clear data between tests
beforeEach(async () => {
    const collections = mongoose.connection.collections;
    for (const key in collections) {
        await collections[key].deleteMany();
    }
});

// Disconnect after all tests
afterAll(async () => {
    await mongoose.disconnect();
    await mongoServer.stop();
});

// Global test utilities
global.testUtils = {
    // Create test user with given role
    async createTestUser(role = 'doctor', status = 'active') {
        let staffId;

        if (role === 'doctor') {
            const doctor = await Doctor.create({
                doctorId: 'DR001',
                personalInfo: {
                    fullName: 'Test Doctor',
                    gender: 'male',
                    dateOfBirth: new Date('1980-01-01'),
                    idNumber: '123456789'
                },
                professionalInfo: {
                    specialization: 'General',
                    qualification: ['MD'],
                    licenseNumber: 'LICENSE001',
                    experience: 10
                }
            });
            staffId = doctor._id;
        }

        const user = await User.create({
            username: `test${role}`,
            passwordHash: await hashPassword('password123'),
            role,
            staffId,
            status
        });

        return { user, staffId };
    },

    // Create test patient
    async createTestPatient() {
        return await Patient.create({
            patientId: 'PT001',
            personalInfo: {
                fullName: 'Test Patient',
                gender: 'male',
                dateOfBirth: new Date('1990-01-01'),
                idNumber: '987654321',
                address: 'Test Address',
                phone: '1234567890'
            },
            healthInfo: {
                bloodType: 'A+',
                allergies: ['Penicillin'],
                chronicDiseases: []
            }
        });
    },

    // Generate test dates
    dates: {
        today: new Date(),
        tomorrow: new Date(Date.now() + 24 * 60 * 60 * 1000),
        nextWeek: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000),
        lastWeek: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
        futureDate: new Date('2025-12-31')
    },

    // Format date for comparisons
    formatDate(date) {
        return new Date(date).toISOString().split('T')[0];
    },

    // Create test file
    createTestFile(filename = 'test.txt', content = 'Test content') {
        const fs = require('fs');
        const path = require('path');
        const filePath = path.join(__dirname, filename);
        fs.writeFileSync(filePath, content);
        return filePath;
    },

    // Clean up test file
    removeTestFile(filename) {
        const fs = require('fs');
        const path = require('path');
        const filePath = path.join(__dirname, filename);
        if (fs.existsSync(filePath)) {
            fs.unlinkSync(filePath);
        }
    },

    // Generate random string
    randomString(length = 10) {
        return Math.random().toString(36).substring(2, length + 2);
    },

    // Generate test appointment data
    generateAppointmentData(patientId, doctorId, date = new Date()) {
        return {
            patientId,
            doctorId,
            appointmentDate: date,
            timeSlot: {
                start: new Date(date.setHours(9, 0, 0)),
                end: new Date(date.setHours(9, 30, 0))
            },
            type: 'new',
            reason: 'Test appointment'
        };
    },

    // Generate test medical record data
    generateMedicalRecordData(patientId, doctorId) {
        return {
            patientId,
            doctorId,
            visitDate: new Date(),
            symptoms: ['Test symptom'],
            diagnosis: ['Test diagnosis'],
            treatment: {
                medications: [{
                    name: 'Test medication',
                    dosage: '100mg',
                    frequency: 'Once daily',
                    duration: '7 days'
                }],
                procedures: [{
                    name: 'Test procedure',
                    notes: 'Test notes'
                }]
            },
            notes: 'Test medical record'
        };
    },

    // Wait for a specified time
    wait(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
};

// Add custom jest matchers
expect.extend({
    toBeWithinRange(received, floor, ceiling) {
        const pass = received >= floor && received <= ceiling;
        if (pass) {
            return {
                message: () => `expected ${received} not to be within range ${floor} - ${ceiling}`,
                pass: true
            };
        } else {
            return {
                message: () => `expected ${received} to be within range ${floor} - ${ceiling}`,
                pass: false
            };
        }
    }
});