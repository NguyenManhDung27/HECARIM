const request = require('supertest');
const mongoose = require('mongoose');
const { MongoMemoryServer } = require('mongodb-memory-server');
const app = require('../app');
const User = require('../models/user.model');
const Doctor = require('../models/doctor.model');
const { hashPassword } = require('../utils/auth');

let mongoServer;

beforeAll(async () => {
    mongoServer = await MongoMemoryServer.create();
    const mongoUri = mongoServer.getUri();
    await mongoose.connect(mongoUri);
});

beforeEach(async () => {
    // Clear database before each test
    await User.deleteMany({});
    await Doctor.deleteMany({});
});

afterAll(async () => {
    await mongoose.disconnect();
    await mongoServer.stop();
});

describe('Authentication Routes', () => {
    describe('POST /api/auth/login', () => {
        it('should login with valid credentials', async () => {
            // Create a test doctor
            const doctor = await Doctor.create({
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
                    experience: 10
                }
            });

            // Create a test user
            await User.create({
                username: 'testdoctor',
                passwordHash: await hashPassword('password123'),
                role: 'doctor',
                staffId: doctor._id,
                status: 'active'
            });

            const response = await request(app)
                .post('/api/auth/login')
                .send({
                    username: 'testdoctor',
                    password: 'password123'
                });

            expect(response.status).toBe(200);
            expect(response.body).toHaveProperty('token');
            expect(response.body.user).toHaveProperty('role', 'doctor');
        });

        it('should fail with invalid credentials', async () => {
            const response = await request(app)
                .post('/api/auth/login')
                .send({
                    username: 'wronguser',
                    password: 'wrongpass'
                });

            expect(response.status).toBe(401);
            expect(response.body).toHaveProperty('message', 'Invalid credentials');
        });

        it('should fail with inactive account', async () => {
            // Create an inactive user
            await User.create({
                username: 'inactiveuser',
                passwordHash: await hashPassword('password123'),
                role: 'doctor',
                status: 'inactive'
            });

            const response = await request(app)
                .post('/api/auth/login')
                .send({
                    username: 'inactiveuser',
                    password: 'password123'
                });

            expect(response.status).toBe(403);
            expect(response.body).toHaveProperty('message', 'Account is inactive');
        });
    });

    describe('POST /api/auth/logout', () => {
        it('should successfully logout', async () => {
            // Create and login a user first
            const doctor = await Doctor.create({
                doctorId: 'DR001',
                personalInfo: {
                    fullName: 'Test Doctor',
                    gender: 'male',
                    dateOfBirth: new Date('1980-01-01'),
                    idNumber: '123456789'
                }
            });

            const user = await User.create({
                username: 'testdoctor',
                passwordHash: await hashPassword('password123'),
                role: 'doctor',
                staffId: doctor._id,
                status: 'active'
            });

            const loginResponse = await request(app)
                .post('/api/auth/login')
                .send({
                    username: 'testdoctor',
                    password: 'password123'
                });

            const token = loginResponse.body.token;

            const response = await request(app)
                .post('/api/auth/logout')
                .set('Authorization', `Bearer ${token}`);

            expect(response.status).toBe(200);
            expect(response.body).toHaveProperty('message', 'Logged out successfully');
        });

        it('should fail without authentication', async () => {
            const response = await request(app)
                .post('/api/auth/logout');

            expect(response.status).toBe(401);
        });
    });

    describe('GET /api/auth/me', () => {
        it('should return current user info', async () => {
            // Create and login a user first
            const doctor = await Doctor.create({
                doctorId: 'DR001',
                personalInfo: {
                    fullName: 'Test Doctor',
                    gender: 'male',
                    dateOfBirth: new Date('1980-01-01'),
                    idNumber: '123456789'
                }
            });

            const user = await User.create({
                username: 'testdoctor',
                passwordHash: await hashPassword('password123'),
                role: 'doctor',
                staffId: doctor._id,
                status: 'active'
            });

            const loginResponse = await request(app)
                .post('/api/auth/login')
                .send({
                    username: 'testdoctor',
                    password: 'password123'
                });

            const token = loginResponse.body.token;

            const response = await request(app)
                .get('/api/auth/me')
                .set('Authorization', `Bearer ${token}`);

            expect(response.status).toBe(200);
            expect(response.body.user).toHaveProperty('username', 'testdoctor');
            expect(response.body.user).toHaveProperty('role', 'doctor');
        });

        it('should fail without authentication', async () => {
            const response = await request(app)
                .get('/api/auth/me');

            expect(response.status).toBe(401);
        });
    });
});