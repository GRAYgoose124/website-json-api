/**
 * Jest setup file for integration API tests (no fetch or storage mocks)
 */
// Polyfill fetch for Node.js environment
const fetch = require('node-fetch');
global.fetch = fetch; 