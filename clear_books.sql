-- Clear all books and related data from the database
-- Run this with: psql -U bookuser -d book_library -f clear_books.sql

BEGIN;

-- Delete in correct order to respect foreign key constraints
DELETE FROM reading_progress;
DELETE FROM favorites;
DELETE FROM reviews;
DELETE FROM book_authors;
DELETE FROM book_genres;
DELETE FROM books;

-- Optionally delete orphaned authors and genres
DELETE FROM authors WHERE id NOT IN (SELECT DISTINCT author_id FROM book_authors);
DELETE FROM genres WHERE id NOT IN (SELECT DISTINCT genre_id FROM book_genres);

-- Show final counts
SELECT 'Books remaining: ' || COUNT(*) FROM books;
SELECT 'Authors remaining: ' || COUNT(*) FROM authors;
SELECT 'Genres remaining: ' || COUNT(*) FROM genres;
SELECT 'Reviews remaining: ' || COUNT(*) FROM reviews;

COMMIT;

-- Vacuum to reclaim space
VACUUM ANALYZE books;
VACUUM ANALYZE authors;
VACUUM ANALYZE genres;
VACUUM ANALYZE reviews;
