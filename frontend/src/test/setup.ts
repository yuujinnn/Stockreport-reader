import '@testing-library/jest-dom';

// Mock window.URL.createObjectURL
Object.defineProperty(window.URL, 'createObjectURL', {
  value: () => 'blob:mock-url',
}); 