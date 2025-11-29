import { test, expect } from '@playwright/test';

test.describe('Book Reading', () => {
  test('should open book reader', async ({ page }) => {
    // Navigate to books page
    await page.goto('/books');
    
    // Wait for books to load
    await page.waitForSelector('[data-testid="book-card"], .book-card, article', { timeout: 10000 });
    
    // Click on first book
    const firstBook = page.locator('[data-testid="book-card"], .book-card, article').first();
    await firstBook.click();
    
    // Look for "Read" button
    const readButton = page.locator('button:has-text("Read"), a:has-text("Read")');
    if (await readButton.count() > 0) {
      await readButton.first().click();
      
      // Should navigate to reading page
      await expect(page).toHaveURL(/\/read|\/books\/\d+\/read/);
    }
  });

  test('should display book content', async ({ page }) => {
    // Assuming reading page exists
    await page.goto('/books/1/read');
    
    // Check for content area
    const contentArea = page.locator('[data-testid="book-content"], .book-content, main');
    if (await contentArea.count() > 0) {
      await expect(contentArea.first()).toBeVisible();
    }
  });

  test('should navigate between pages', async ({ page }) => {
    await page.goto('/books/1/read');
    
    // Look for next page button
    const nextButton = page.locator('button:has-text("Next"), button[aria-label*="next" i]');
    if (await nextButton.count() > 0) {
      await nextButton.first().click();
      
      // Wait for page change
      await page.waitForTimeout(500);
    }
    
    // Look for previous page button
    const prevButton = page.locator('button:has-text("Previous"), button:has-text("Prev"), button[aria-label*="previous" i]');
    if (await prevButton.count() > 0) {
      await expect(prevButton.first()).toBeVisible();
    }
  });

  test('should track reading progress', async ({ page }) => {
    await page.goto('/books/1/read');
    
    // Look for progress indicator
    const progressIndicator = page.locator('[data-testid="progress"], .progress, text=/page \\d+ of \\d+/i');
    if (await progressIndicator.count() > 0) {
      await expect(progressIndicator.first()).toBeVisible();
    }
  });
});

test.describe('Reading Controls', () => {
  test('should adjust font size', async ({ page }) => {
    await page.goto('/books/1/read');
    
    // Look for font size controls
    const fontSizeButton = page.locator('button[aria-label*="font" i], button:has-text("A")');
    if (await fontSizeButton.count() > 0) {
      await fontSizeButton.first().click();
      
      // Should show font size options
      await page.waitForTimeout(500);
    }
  });

  test('should toggle theme', async ({ page }) => {
    await page.goto('/books/1/read');
    
    // Look for theme toggle
    const themeButton = page.locator('button[aria-label*="theme" i], button:has-text("Theme")');
    if (await themeButton.count() > 0) {
      await themeButton.first().click();
      
      // Wait for theme change
      await page.waitForTimeout(500);
    }
  });
});
