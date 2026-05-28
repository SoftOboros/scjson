module.exports = {
  testEnvironment: 'node',
  // TypeScript fixtures (e.g. tests/help_text_consumer.test.ts) are
  // compilation-only smokes meant for ``npx tsc --noEmit``; jest does not
  // load a TS transformer, so restrict its discovery to JavaScript tests.
  testMatch: ['**/tests/**/*.test.js'],
};
