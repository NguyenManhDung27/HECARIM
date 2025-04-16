const request = require('supertest');
const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');
const app = require('../app');
const User = require('../models/user.model');
const Patient = require('../models/patient.model');
const Doctor = require('../models/doctor.model');
const Appointment = require('../models/appointment.model');
const { hashPassword } = require('../utils/auth');

let mongoServer;
let authToken;
let testDoctor;
let testPatient;

beforeAll(async () => {
    mongoServer = await MongoMemoryServer.create();
    const mongoUri = mongoServer.getUri();
    await mongoose.connect(mongoUri);

    // Create test user
    const user = await User.create({
        username: 'testreceptionist',
        passwordHash: await hashPassword('password123'),
        role: 'receptionist',
        status: 'active'
    });

    const loginResponse = await request(app)
        .post('/api/auth/login')
        .send({
            username: 'testreceptionist',
            password: 'password123'
        });

    authToken = loginResponse.body.token;

    // Create test doctor
    testDoctor = await Doctor.create({
        doctorId: 'DR001',
        personalInfo: {
            fullName: 'Test Doctor',
            gender: 'male',
            dateOfBirth: new Date('1980-01-01'),
            idNumber: '123456789',
            address: 'Test Address',
            phone: '1234567890'
        },
        professionalInfo: {
            specialization: 'General',
            qualification: ['MD'],
            licenseNumber: 'LICENSE001',
            experience: 10,
            department: 'General Medicine'
        }
    });

    // Create test patient
    testPatient = await Patient.create({
        patientId: 'PT001',
        personalInfo: {
            fullName: 'Test Patient',
            gender: 'male',
            dateOfBirth: new Date('1990-01-01'),
            idNumber: '987654321',
            address: 'Test Address',
            phone: '0987654321'
        }
    });
});

beforeEach(async () => {
    await Appointment.deleteMany({});
});

afterAll(async () => {
    await mongoose.disconnect();
    await mongoServer.stop();
});

describe('Appointment Routes', () => {
    describe('GET /api/appointments', () => {
        it('should return list of appointments', async () => {
            // Create test appointments
            await Appointment.create([
                {
                    appointmentId: 'APT001',
                    patientId: testPatient._id,
                    doctorId: testDoctor._id,
                    date: new Date('2025-04-20'),
                    timeSlot: {
                        start: new Date('2025-04-20T09:00:00Z'),
                        end: new Date('2025-04-20T09:30:00Z')
                    },
                    status: 'scheduled',
                    type: 'new',
                    reason: 'General checkup'
                },
                {
                    appointmentId: 'APT002',
                    patientId: testPatient._id,
                    doctorId: testDoctor._id,
                    date: new Date('2025-04-21'),
                    timeSlot: {
                        start: new Date('2025-04-21T10:00:00Z'),
                        end: new Date('2025-04-21T10:30:00Z')
                    },
                    status: 'scheduled',
                    type: 'follow-up',
                    reason: 'Follow-up checkup'
                }
            ]);

            const response = await request(app)
                .get('/api/appointments')
                .set('Authorization', `Bearer ${authToken}`);

            expect(response.status).toBe(200);
            expect(response.body.data).toHaveLength(2);
            expect(response.body.data[0]).toHaveProperty('appointmentId');
        });

        it('should filter appointments by date', async () => {
            await Appointment.create([
                {
                    appointmentId: 'APT001',
                    patientId: testPatient._id,
                    doctorId: testDoctor._id,
                    date: new Date('2025-04-20'),
                    timeSlot: {
                        start: new Date('2025-04-20T09:00:00Z'),
                        end: new Date('2025-04-20T09:30:00Z')
                    },
                    status: 'scheduled'
                },
                {
                    appointmentId: 'APT002',
                    patientId: testPatient._id,
                    doctorId: testDoctor._id,
                    date: new Date('2025-04-21'),
                    timeSlot: {
                        start: new Date('2025-04-21T10:00:00Z'),
                        end: new Date('2025-04-21T10:30:00Z')
                    },
                    status: 'scheduled'
                }
            ]);

            const response = await request(app)
                .get('/api/appointments?date=2025-04-20')
                .set('Authorization', `Bearer ${authToken}`);

            expect(response.status).toBe(200);
            expect(response.body.data).toHaveLength(1);
            expect(response.body.data[0].appointmentId).toBe('APT001');
        });
    });

    describe('POST /api/appointments', () => {
        it('should create new appointment', async () => {
            const appointmentData = {
                patientId: testPatient._id,
                doctorId: testDoctor._id,
                date: '2025-04-20',
                timeSlot: {
                    start: '2025-04-20T09:00:00Z',
                    end: '2025-04-20T09:30:00Z'
                },
                type: 'new',
                reason: 'General checkup'
            };

            const response = await request(app)
                .post('/api/appointments')
                .set('Authorization', `Bearer ${authToken}`)
                .send(appointmentData);

            expect(response.status).toBe(201);
            expect(response.body.data).toHaveProperty('appointmentId');
            expect(response.body.data.status).toBe('scheduled');
        });

        it('should prevent scheduling conflicting appointments', async () => {
            // Create an existing appointment
            await Appointment.create({
                appointmentId: 'APT001',
                patientId: testPatient._id,
                doctorId: testDoctor._id,
                date: new Date('2025-04-20'),
                timeSlot: {
                    start: new Date('2025-04-20T09:00:00Z'),
                    end: new Date('2025-04-20T09:30:00Z')
                },
                status: 'scheduled'
            });

            // Try to create conflicting appointment
            const response = await request(app)
                .post('/api/appointments')
                .set('Authorization', `Bearer ${authToken}`)
                .send({
                    patientId: testPatient._id,
                    doctorId: testDoctor._id,
                    date: '2025-04-20',
                    timeSlot: {
                        start: '2025-04-20T09:00:00Z',
                        end: '2025-04-20T09:30:00Z'
                    }
                });

            expect(response.status).toBe(400);
            expect(response.body.message).toContain('conflict');
        });
    });

    describe('PATCH /api/appointments/:id/status', () => {
        it('should update appointment status', async () => {
            const appointment = await Appointment.create({
                appointmentId: 'APT001',
                patientId: testPatient._id,
                doctorId: testDoctor._id,
                date: new Date('2025-04-20'),
                timeSlot: {
                    start: new Date('2025-04-20T09:00:00Z'),
                    end: new Date('2025-04-20T09:30:00Z')
                },
                status: 'scheduled'
            });

            const response = await request(app)
                .patch(`/api/appointments/${appointment._id}/status`)
                .set('Authorization', `Bearer ${authToken}`)
                .send({ status: 'completed' });

            expect(response.status).toBe(200);
            expect(response.body.data.status).toBe('completed');
        });

        it('should validate status transitions', async () => {
            const appointment = await Appointment.create({
                appointmentId: 'APT001',
                patientId: testPatient._id,
                doctorId: testDoctor._id,
                date: new Date('2025-04-20'),
                timeSlot: {
                    start: new Date('2025-04-20T09:00:00Z'),
                    end: new Date('2025-04-20T09:30:00Z')
                },
                status: 'completed'
            });

            const response = await request(app)
                .patch(`/api/appointments/${appointment._id}/status`)
                .set('Authorization', `Bearer ${authToken}`)
                .send({ status: 'scheduled' });

            expect(response.status).toBe(400);
            expect(response.body.message).toContain('Invalid status transition');
        });
    });

    describe('DELETE /api/appointments/:id', () => {
        it('should cancel appointment', async () => {
            const appointment = await Appointment.create({
                appointmentId: 'APT001',
                patientId: testPatient._id,
                doctorId: testDoctor._id,
                date: new Date('2025-04-20'),
                timeSlot: {
                    start: new Date('2025-04-20T09:00:00Z'),
                    end: new Date('2025-04-20T09:30:00Z')
                },
                status: 'scheduled'
            });

            const response = await request(app)
                .delete(`/api/appointments/${appointment._id}`)
                .set('Authorization', `Bearer ${authToken}`);

            expect(response.status).toBe(200);
            
            const cancelledAppointment = await Appointment.findById(appointment._id);
            expect(cancelledAppointment.status).toBe('cancelled');
        });

        it('should not allow cancelling completed appointments', async () => {
            const appointment = await Appointment.create({
                appointmentId: 'APT001',
                patientId: testPatient._id,
                doctorId: testDoctor._id,
                date: new Date('2025-04-20'),
                timeSlot: {
                    start: new Date('2025-04-20T09:00:00Z'),
                    end: new Date('2025-04-20T09:30:00Z')
                },
                status: 'completed'
            });

            const response = await request(app)
                .delete(`/api/appointments/${appointment._id}`)
                .set('Authorization', `Bearer ${authToken}`);

            expect(response.status).toBe(400);
            expect(response.body.message).toContain('Cannot cancel completed appointment');
        });
    });
});