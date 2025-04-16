module.exports = {
    // Test environment
    testEnvironment: 'node',

    // Test match patterns
    testMatch: ['**/tests/**/*.test.js'],

    // Coverage configuration
    collectCoverage: true,
    coverageDirectory: 'coverage',
    collectCoverageFrom: [
        'routes/**/*.js',
        'models/**/*.js',
        'middleware/**/*.js',
        'utils/**/*.js',
        '!**/node_modules/**'
    ],
    coverageReporters: ['text', 'lcov'],

    // Setup files
    setupFilesAfterEnv: ['./tests/setup.js'],

    // Test timeout
    testTimeout: 10000,

    // Verbose output
    verbose: true,

    // Clear mock calls between every test
    clearMocks: true,

    // Environment variables for testing
    testEnvironmentVariables: {
        NODE_ENV: 'test',
        JWT_SECRET: 'test-secret-key',
        PORT: '5000'
    }
};