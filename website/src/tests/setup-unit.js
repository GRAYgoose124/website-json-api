/**
 * Jest setup file for unit API tests (mocks fetch, localStorage, etc.)
 */

// Mock localStorage for Node.js environment
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Mock FormData for Node.js environment
global.FormData = class FormData {
  constructor() {
    this.data = new Map();
  }
  append(key, value) {
    this.data.set(key, value);
  }
  get(key) {
    return this.data.get(key);
  }
  has(key) {
    return this.data.has(key);
  }
  delete(key) {
    this.data.delete(key);
  }
  entries() {
    return this.data.entries();
  }
  keys() {
    return this.data.keys();
  }
  values() {
    return this.data.values();
  }
};

// Mock File for Node.js environment
global.File = class File {
  constructor(bits, name, options = {}) {
    this.name = name;
    this.type = options.type || 'text/plain';
    this.size = bits.length;
    this.content = bits;
  }
  arrayBuffer() {
    return Promise.resolve(this.content);
  }
  text() {
    return Promise.resolve(this.content.toString());
  }
  stream() {
    // Mock stream implementation
    return {
      getReader() {
        return {
          read() {
            return Promise.resolve({ done: true, value: undefined });
          }
        };
      }
    };
  }
};

// Mock fetch globally
global.fetch = jest.fn();

// Reset all mocks before each test
beforeEach(() => {
  jest.clearAllMocks();
  localStorageMock.getItem.mockClear();
  localStorageMock.setItem.mockClear();
  localStorageMock.removeItem.mockClear();
  localStorageMock.clear.mockClear();
}); 