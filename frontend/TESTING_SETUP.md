# Frontend Testing Setup Guide

## Overview

This guide explains how to set up and run tests for the BookLook frontend application.

## Testing Stack

For Next.js 16 with React 19, we recommend:

- **Jest**: Test runner
- **React Testing Library**: Component testing
- **Playwright**: E2E testing

## Installation

### 1. Install Jest and React Testing Library

```bash
cd frontend
npm install --save-dev jest jest-environment-jsdom @testing-library/react @testing-library/jest-dom @testing-library/user-event
npm install --save-dev @types/jest
```

### 2. Install Playwright for E2E Tests

```bash
cd frontend
npm install --save-dev @playwright/test
npx playwright install
```

## Configuration

### Jest Configuration

Create `jest.config.js`:

```javascript
const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app
  dir: './',
})

const customJestConfig = {
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
  testEnvironment: 'jest-environment-jsdom',
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/$1',
  },
  testMatch: [
    '**/__tests__/**/*.[jt]s?(x)',
    '**/?(*.)+(spec|test).[jt]s?(x)'
  ],
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
  ],
}

module.exports = createJestConfig(customJestConfig)
```

Create `jest.setup.js`:

```javascript
import '@testing-library/jest-dom'
```

### Playwright Configuration

Create `playwright.config.ts`:

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

### Update package.json

Add test scripts to `package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui"
  }
}
```

## Example Tests

### Component Test Example

Create `src/components/__tests__/Button.test.tsx`:

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

describe('Button Component', () => {
  it('renders button with text', () => {
    render(<button>Click me</button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('calls onClick when clicked', async () => {
    const handleClick = jest.fn();
    render(<button onClick={handleClick}>Click me</button>);
    
    await userEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});
```

### E2E Test Example

Create `e2e/login.spec.ts`:

```typescript
import { test, expect } from '@playwright/test';

test('user can login', async ({ page }) => {
  await page.goto('/login');
  
  await page.fill('input[name="email"]', 'test@example.com');
  await page.fill('input[name="password"]', 'password123');
  await page.click('button[type="submit"]');
  
  await expect(page).toHaveURL('/dashboard');
});
```

## Running Tests

### Unit/Component Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

### E2E Tests

```bash
# Run E2E tests
npm run test:e2e

# Run E2E tests with UI
npm run test:e2e:ui

# Run specific test file
npx playwright test e2e/login.spec.ts
```

## Test Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── __tests__/
│   │   │   ├── Button.test.tsx
│   │   │   └── BookCard.test.tsx
│   │   ├── Button.tsx
│   │   └── BookCard.tsx
│   └── app/
│       └── __tests__/
│           └── page.test.tsx
├── e2e/
│   ├── login.spec.ts
│   ├── books.spec.ts
│   └── reading.spec.ts
├── jest.config.js
├── jest.setup.js
└── playwright.config.ts
```

## Best Practices

### Component Tests
1. Test user interactions, not implementation details
2. Use accessible queries (getByRole, getByLabelText)
3. Test error states and loading states
4. Mock API calls and external dependencies

### E2E Tests
1. Test critical user journeys
2. Keep tests independent
3. Use data-testid sparingly
4. Clean up test data after each test

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: npm ci
        working-directory: ./frontend
      
      - name: Run unit tests
        run: npm test
        working-directory: ./frontend
      
      - name: Run E2E tests
        run: npm run test:e2e
        working-directory: ./frontend
```

## Troubleshooting

### Common Issues

1. **Module not found errors**: Check `moduleNameMapper` in jest.config.js
2. **Next.js specific features not working**: Ensure you're using `next/jest`
3. **Playwright tests failing**: Make sure dev server is running on port 3000

## Next Steps

1. Install testing dependencies
2. Create jest.config.js and playwright.config.ts
3. Write component tests for critical components
4. Write E2E tests for main user flows
5. Integrate tests into CI/CD pipeline

## Resources

- [Jest Documentation](https://jestjs.io/)
- [React Testing Library](https://testing-library.com/react)
- [Playwright Documentation](https://playwright.dev/)
- [Next.js Testing Guide](https://nextjs.org/docs/testing)
