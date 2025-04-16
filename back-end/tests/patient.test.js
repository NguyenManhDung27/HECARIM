const request = require('supertest');
const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');
const app = require('../app');
const User = require('../models/user.model');
const Patient = require('../models/patient.model');
const { hashPassword } = require('../utils/auth');

let mongoServer;
let authToken;

beforeAll(async () => {
    mongoServer = await MongoMemoryServer.create();
    const mongoUri = mongoServer.getUri();
    await mongoose.connect(mongoUri);

    // Create test user and get auth token
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
});

beforeEach(async () => {
    await Patient.deleteMany({});
});

afterAll(async () => {
    await mongoose.disconnect();
    await mongoServer.stop();
});

describe('Patient Routes', () => {
    describe('GET /api/patients', () => {
        it('should return list of patients', async () => {
            // Create test patients
            await Patient.create([
                {
                    patientId: 'PT001',
                    personalInfo: {
                        fullName: 'Test Patient 1',
                        gender: 'male',
                        dateOfBirth: new Date('1990-01-01'),
                        idNumber: '123456789',
                        address: 'Test Address 1',
                        phone: '1234567890'
                    }
                },
                {
                    patientId: 'PT002',
                    personalInfo: {
                        fullName: 'Test Patient 2',
                        gender: 'female',
                        dateOfBirth: new Date('1992-01-01'),
                        idNumber: '987654321',
                        address: 'Test Address 2',
                        phone: '0987654321'
                    }
                }
            ]);

            const response = await request(app)
                .get('/api/patients')
                .set('Authorization', `Bearer ${authToken}`);

            expect(response.status).toBe(200);
            expect(response.body.data).toHaveLength(2);
            expect(response.body.data[0]).toHaveProperty('patientId');
            expect(response.body.data[0].personalInfo).toHaveProperty('fullName');
        });

        it('should support pagination', async () => {
            // Create 15 test patients
            const patients = Array.from({ length: 15 }, (_, i) => ({
                patientId: `PT${String(i + 1).padStart(3, '0')}`,
                personalInfo: {
                    fullName: `Test Patient ${i + 1}`,
                    gender: 'male',
                    dateOfBirth: new Date('1990-01-01'),
                    idNumber: `${1000000 + i}`,
                    address: `Test Address ${i + 1}`,
                    phone: `123456${i}`
                }
            }));

            await Patient.create(patients);

            const response = await request(app)
                .get('/api/patients?page=1&limit=10')
                .set('Authorization', `Bearer ${authToken}`);

            expect(response.status).toBe(200);
            expect(response.body.data).toHaveLength(10);
            expect(response.body.pagination).toEqual({
                total: 15,
                page: 1,
                pages: 2
            });
        });

        it('should support search by name', async () => {
            await Patient.create([
                {
                    patientId: 'PT001',
                    personalInfo: {
                        fullName: 'John Doe',
                        gender: 'male',
                        dateOfBirth: new Date('1990-01-01'),
                        idNumber: '123456789'
                    }
                },
                {
                    patientId: 'PT002',
                    personalInfo: {
                        fullName: 'Jane Smith',
                        gender: 'female',
                        dateOfBirth: new Date('1992-01-01'),
                        idNumber: '987654321'
                    }
                }
            ]);

            const response = await request(app)
                .get('/api/patients?search=john')
                .set('Authorization', `Bearer ${authToken}`);

            expect(response.status).toBe(200);
            expect(response.body.data).toHaveLength(1);
            expect(response.body.data[0].personalInfo.fullName).toBe('John Doe');
        });
    });

    describe('POST /api/patients', () => {
        it('should create new patient', async () => {
            const patientData = {
                personalInfo: {
                    fullName: 'New Patient',
                    gender: 'male',
                    dateOfBirth: '1990-01-01',
                    idNumber: '123456789',
                    address: 'Test Address',
                    phone: '1234567890',
                    email: 'test@example.com'
                },
                healthInfo: {
                    bloodType: 'A+',
                    allergies: ['Penicillin'],
                    chronicDiseases: []
                },
                insurance: {
                    provider: 'Test Insurance',
                    policyNumber: 'INS123',
                    expiryDate: '2025-12-31'
                }
            };

            const response = await request(app)
                .post('/api/patients')
                .set('Authorization', `Bearer ${authToken}`)
                .send(patientData);

            expect(response.status).toBe(201);
            expect(response.body.data).toHaveProperty('patientId');
            expect(response.body.data.personalInfo.fullName).toBe('New Patient');
        });

        it('should validate required fields', async () => {
            const response = await request(app)
                .post('/api/patients')
                .set('Authorization', `Bearer ${authToken}`)
                .send({
                    personalInfo: {
                        gender: 'male'
                    }
                });

            expect(response.status).toBe(400);
            expect(response.body).toHaveProperty('errors');
            expect(response.body.errors).toHaveProperty('personalInfo.fullName');
        });

        it('should prevent duplicate ID numbers', async () => {
            const patientData = {
                personalInfo: {
                    fullName: 'Test Patient',
                    gender: 'male',
                    dateOfBirth: '1990-01-01',
                    idNumber: '123456789',
                    address: 'Test Address',
                    phone: '1234567890'
                }
            };

            await Patient.create(patientData);

            const response = await request(app)
                .post('/api/patients')
                .set('Authorization', `Bearer ${authToken}`)
                .send(patientData);

            expect(response.status).toBe(400);
            expect(response.body.message).toContain('duplicate');
        });
    });

    describe('PUT /api/patients/:id', () => {
        it('should update existing patient', async () => {
            const patient = await Patient.create({
                patientId: 'PT001',
                personalInfo: {
                    fullName: 'Test Patient',
                    gender: 'male',
                    dateOfBirth: new Date('1990-01-01'),
                    idNumber: '123456789',
                    address: 'Test Address',
                    phone: '1234567890'
                }
            });

            const response = await request(app)
                .put(`/api/patients/${patient._id}`)
                .set('Authorization', `Bearer ${authToken}`)
                .send({
                    personalInfo: {
                        fullName: 'Updated Name',
                        phone: '0987654321'
                    }
                });

            expect(response.status).toBe(200);
            expect(response.body.data.personalInfo.fullName).toBe('Updated Name');
            expect(response.body.data.personalInfo.phone).toBe('0987654321');
        });

        it('should return 404 for non-existent patient', async () => {
            const response = await request(app)
                .put(`/api/patients/${new mongoose.Types.ObjectId()}`)
                .set('Authorization', `Bearer ${authToken}`)
                .send({
                    personalInfo: {
                        fullName: 'Updated Name'
                    }
                });

            expect(response.status).toBe(404);
        });
    });

    describe('DELETE /api/patients/:id', () => {
        it('should delete patient', async () => {
            const patient = await Patient.create({
                patientId: 'PT001',
                personalInfo: {
                    fullName: 'Test Patient',
                    gender: 'male',
                    dateOfBirth: new Date('1990-01-01'),
                    idNumber: '123456789'
                }
            });

            const response = await request(app)
                .delete(`/api/patients/${patient._id}`)
                .set('Authorization', `Bearer ${authToken}`);

            expect(response.status).toBe(200);
            
            const deletedPatient = await Patient.findById(patient._id);
            expect(deletedPatient).toBeNull();
        });

        it('should return 404 for non-existent patient', async () => {
            const response = await request(app)
                .delete(`/api/patients/${new mongoose.Types.ObjectId()}`)
                .set('Authorization', `Bearer ${authToken}`);

            expect(response.status).toBe(404);
        });
    });
});