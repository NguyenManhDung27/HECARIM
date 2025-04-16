const request = require('supertest');
const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');
const fs = require('fs');
const path = require('path');
const app = require('../app');
const User = require('../models/user.model');
const Patient = require('../models/patient.model');
const Doctor = require('../models/doctor.model');
const MedicalRecord = require('../models/medicalRecord.model');
const { hashPassword } = require('../utils/auth');

let mongoServer;
let doctorToken;
let testDoctor;
let testPatient;
let testRecord;

beforeAll(async () => {
    mongoServer = await MongoMemoryServer.create();
    const mongoUri = mongoServer.getUri();
    await mongoose.connect(mongoUri);

    // Create test doctor
    testDoctor = await Doctor.create({
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
            licenseNumber: 'LICENSE001'
        }
    });

    // Create doctor user and get token
    const doctorUser = await User.create({
        username: 'testdoctor',
        passwordHash: await hashPassword('password123'),
        role: 'doctor',
        staffId: testDoctor._id,
        status: 'active'
    });

    const loginResponse = await request(app)
        .post('/api/auth/login')
        .send({
            username: 'testdoctor',
            password: 'password123'
        });

    doctorToken = loginResponse.body.token;

    // Create test patient
    testPatient = await Patient.create({
        patientId: 'PT001',
        personalInfo: {
            fullName: 'Test Patient',
            gender: 'male',
            dateOfBirth: new Date('1990-01-01'),
            idNumber: '987654321'
        }
    });
});

beforeEach(async () => {
    await MedicalRecord.deleteMany({});
});

afterAll(async () => {
    await mongoose.disconnect();
    await mongoServer.stop();
});

describe('Medical Record Routes', () => {
    describe('POST /api/medical-records', () => {
        it('should create new medical record', async () => {
            const recordData = {
                patientId: testPatient._id,
                visitDate: new Date(),
                symptoms: ['Headache', 'Fever'],
                diagnosis: ['Common cold'],
                treatment: {
                    medications: [{
                        name: 'Paracetamol',
                        dosage: '500mg',
                        frequency: '3 times/day',
                        duration: '5 days'
                    }],
                    procedures: [{
                        name: 'Temperature check',
                        notes: 'Normal temperature'
                    }]
                },
                notes: 'Rest and hydration recommended'
            };

            const response = await request(app)
                .post('/api/medical-records')
                .set('Authorization', `Bearer ${doctorToken}`)
                .send(recordData);

            expect(response.status).toBe(201);
            expect(response.body.data).toHaveProperty('recordId');
            expect(response.body.data.status).toBe('draft');
        });

        it('should validate required fields', async () => {
            const response = await request(app)
                .post('/api/medical-records')
                .set('Authorization', `Bearer ${doctorToken}`)
                .send({
                    patientId: testPatient._id
                });

            expect(response.status).toBe(400);
            expect(response.body.errors).toBeDefined();
        });
    });

    describe('PUT /api/medical-records/:id', () => {
        beforeEach(async () => {
            testRecord = await MedicalRecord.create({
                recordId: 'MR001',
                patientId: testPatient._id,
                doctorId: testDoctor._id,
                visitDate: new Date(),
                symptoms: ['Headache'],
                diagnosis: ['Migraine'],
                status: 'draft'
            });
        });

        it('should update medical record', async () => {
            const updateData = {
                symptoms: ['Headache', 'Nausea'],
                diagnosis: ['Severe migraine'],
                treatment: {
                    medications: [{
                        name: 'Sumatriptan',
                        dosage: '50mg',
                        frequency: 'As needed'
                    }]
                }
            };

            const response = await request(app)
                .put(`/api/medical-records/${testRecord._id}`)
                .set('Authorization', `Bearer ${doctorToken}`)
                .send(updateData);

            expect(response.status).toBe(200);
            expect(response.body.data.symptoms).toContain('Nausea');
            expect(response.body.data.treatment.medications[0].name).toBe('Sumatriptan');
        });

        it('should not update finalized record', async () => {
            await MedicalRecord.findByIdAndUpdate(testRecord._id, { status: 'final' });

            const response = await request(app)
                .put(`/api/medical-records/${testRecord._id}`)
                .set('Authorization', `Bearer ${doctorToken}`)
                .send({ symptoms: ['Updated symptoms'] });

            expect(response.status).toBe(400);
            expect(response.body.message).toContain('finalized');
        });
    });

    describe('POST /api/medical-records/:id/attachments', () => {
        beforeEach(async () => {
            testRecord = await MedicalRecord.create({
                recordId: 'MR001',
                patientId: testPatient._id,
                doctorId: testDoctor._id,
                visitDate: new Date(),
                status: 'draft'
            });
        });

        it('should upload file attachments', async () => {
            // Create test file
            const testFilePath = path.join(__dirname, 'test-file.txt');
            fs.writeFileSync(testFilePath, 'Test content');

            const response = await request(app)
                .post(`/api/medical-records/${testRecord._id}/attachments`)
                .set('Authorization', `Bearer ${doctorToken}`)
                .attach('files', testFilePath);

            expect(response.status).toBe(201);
            expect(response.body.data.attachments).toHaveLength(1);
            expect(response.body.data.attachments[0]).toHaveProperty('filename');

            // Cleanup
            fs.unlinkSync(testFilePath);
        });

        it('should validate file types', async () => {
            // Create invalid file
            const testFilePath = path.join(__dirname, 'test-file.exe');
            fs.writeFileSync(testFilePath, 'Test content');

            const response = await request(app)
                .post(`/api/medical-records/${testRecord._id}/attachments`)
                .set('Authorization', `Bearer ${doctorToken}`)
                .attach('files', testFilePath);

            expect(response.status).toBe(400);
            expect(response.body.message).toContain('file type');

            // Cleanup
            fs.unlinkSync(testFilePath);
        });
    });

    describe('POST /api/medical-records/:id/prescriptions', () => {
        beforeEach(async () => {
            testRecord = await MedicalRecord.create({
                recordId: 'MR001',
                patientId: testPatient._id,
                doctorId: testDoctor._id,
                visitDate: new Date(),
                status: 'draft'
            });
        });

        it('should add prescription', async () => {
            const prescriptionData = {
                medications: [{
                    name: 'Amoxicillin',
                    dosage: '500mg',
                    frequency: '3 times/day',
                    duration: '7 days',
                    quantity: 21
                }]
            };

            const response = await request(app)
                .post(`/api/medical-records/${testRecord._id}/prescriptions`)
                .set('Authorization', `Bearer ${doctorToken}`)
                .send(prescriptionData);

            expect(response.status).toBe(201);
            expect(response.body.data.prescriptions).toHaveLength(1);
            expect(response.body.data.prescriptions[0].medications[0].name).toBe('Amoxicillin');
        });

        it('should validate prescription data', async () => {
            const response = await request(app)
                .post(`/api/medical-records/${testRecord._id}/prescriptions`)
                .set('Authorization', `Bearer ${doctorToken}`)
                .send({
                    medications: [{
                        name: 'Amoxicillin'
                        // Missing required fields
                    }]
                });

            expect(response.status).toBe(400);
            expect(response.body.errors).toBeDefined();
        });
    });

    describe('GET /api/medical-records/patient/:patientId', () => {
        beforeEach(async () => {
            await MedicalRecord.create([
                {
                    recordId: 'MR001',
                    patientId: testPatient._id,
                    doctorId: testDoctor._id,
                    visitDate: new Date('2025-04-15'),
                    symptoms: ['Fever'],
                    status: 'final'
                },
                {
                    recordId: 'MR002',
                    patientId: testPatient._id,
                    doctorId: testDoctor._id,
                    visitDate: new Date('2025-04-16'),
                    symptoms: ['Cough'],
                    status: 'final'
                }
            ]);
        });

        it('should return patient medical history', async () => {
            const response = await request(app)
                .get(`/api/medical-records/patient/${testPatient._id}`)
                .set('Authorization', `Bearer ${doctorToken}`);

            expect(response.status).toBe(200);
            expect(response.body.data).toHaveLength(2);
            expect(response.body.data[0]).toHaveProperty('recordId');
        });

        it('should sort records by date', async () => {
            const response = await request(app)
                .get(`/api/medical-records/patient/${testPatient._id}?sort=desc`)
                .set('Authorization', `Bearer ${doctorToken}`);

            expect(response.status).toBe(200);
            expect(new Date(response.body.data[0].visitDate))
                .toBeGreaterThan(new Date(response.body.data[1].visitDate));
        });
    });
});