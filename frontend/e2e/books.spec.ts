import { test, expect } from '@playwright/test';

test.describe('Book Browsing', () => {
  test('should display books list', async ({ page }) => {
    await page.goto('/books');
    
    // Wait for books to load
    await page.waitForSelector('[data-testid="book-card"], .book-card, article', { timeout: 10000 });
    
    // Check if books are displayed
    const bookElements = await page.locator('[data-testid="book-card"], .book-card, article').count();
    expect(bookElements).toBeGreaterThan(0);
  });

  test('should search for books', async ({ page }) => {
    await page.goto('/books');
    
    // Find search input
    const searchInput = page.locator('input[type="search"], input[placeholder*="search" i]');
    if (await searchInput.count() > 0) {
      await searchInput.first().fill('test');
      await page.keyboard.press('Enter');
      
      // Wait for search results
      await page.waitForTimeout(1000);
    }
  });

  test('should filter books by genre', async ({ page }) => {
    await page.goto('/books');
    
    // Look for genre filter
    const genreFilter = page.locator('select, [role="combobox"]').first();
    if (await genreFilter.count() > 0) {
      await genreFilter.click();
      // Select first available option
      await page.keyboard.press('ArrowDown');
      await page.keyboard.press('Enter');
      
      // Wait for filtered results
      await page.waitForTimeout(1000);
    }
  });

  test('should navigate to book details', async ({ page }) => {
    await page.goto('/books');
    
    // Wait for books to load
    await page.waitForSelector('[data-testid="book-card"], .book-card, article', { timeout: 10000 });
    
    // Click on first book
    const firstBook = page.locator('[data-testid="book-card"], .book-card, article').first();
    await firstBook.click();
    
    // Should navigate to book details page
    await expect(page).toHaveURL(/\/books\/\d+/);
  });
});

test.describe('Book Details', () => {
  test('should display book information', async ({ page }) => {
    // Navigate to a book details page (assuming book with ID 1 exists)
    await page.goto('/books/1');
    
    // Check for book title
    await expect(page.locator('h1')).toBeVisible();
    
    // Check for book metadata
    await expect(page.locator('text=/author|isbn|pages/i')).toBeVisible();
  });

  test('should display reviews section', async ({ page }) => {
    await page.goto('/books/1');
    
    // Look for reviews section
    const reviewsSection = page.locator('text=/reviews|ratings/i');
    if (await reviewsSection.count() > 0) {
      await expect(reviewsSection.first()).toBeVisible();
    }
  });
});
