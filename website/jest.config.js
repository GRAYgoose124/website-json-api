export default {
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: process.env.TEST_ENV === 'integration'
    ? ['<rootDir>/src/tests/setup-integration.js']
    : ['<rootDir>/src/tests/setup-unit.js'],
  testMatch: [
    '<rootDir>/src/tests/**/*.test.js',
    '<rootDir>/src/tests/**/*.test.jsx'
  ],
  collectCoverageFrom: [
    'src/**/*.{js,jsx}',
    '!src/tests/**',
    '!src/main.jsx',
    '!src/index.jsx'
  ],
  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html'],
  moduleNameMapper: {
    '^(\\.{1,2}/.*)\\.js$': '$1',
  },
  transform: {
    '^.+\\.(js|jsx)$': 'babel-jest',
  },
  testTimeout: 30000,
}; 