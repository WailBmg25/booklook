-- ============================================
-- BookLook Database Schema
-- Complete SQL Schema for PostgreSQL 15+
-- ============================================

-- ============================================
-- 1. USERS TABLE
-- ============================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Legacy fields for backward compatibility
    nom VARCHAR(100),
    prenom VARCHAR(100),
    photo_url VARCHAR(500)
);

-- Indexes for users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_active ON users(is_active);

-- ============================================
-- 2. AUTHORS TABLE
-- ============================================
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    prenom VARCHAR(255),
    biographie TEXT,
    photo_url VARCHAR(500),
    date_naissance DATE,
    nationalite VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for authors
CREATE INDEX idx_authors_nom ON authors(nom);
CREATE INDEX idx_authors_prenom ON authors(prenom);
CREATE INDEX idx_authors_full_name ON authors(nom, prenom);

-- ============================================
-- 3. GENRES TABLE
-- ============================================
CREATE TABLE genres (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for genres
CREATE INDEX idx_genres_nom ON genres(nom);

-- ============================================
-- 4. BOOKS TABLE (Optimized for Large Datasets)
-- ============================================
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    titre VARCHAR(500) NOT NULL,
    isbn VARCHAR(20) UNIQUE NOT NULL,
    date_publication DATE,
    description TEXT,
    image_url VARCHAR(500),
    nombre_pages INTEGER,
    langue VARCHAR(50) DEFAULT 'Français',
    editeur VARCHAR(255),
    
    -- Legacy rating fields
    note_moyenne FLOAT DEFAULT 0.0,
    nombre_reviews INTEGER DEFAULT 0,
    
    -- Denormalized fields for performance
    author_names TEXT[],  -- Array of author names
    genre_names TEXT[],   -- Array of genre names
    
    -- Enhanced fields for large dataset
    content_path VARCHAR(500),      -- Path to book content file
    word_count INTEGER,             -- Total word count
    total_pages INTEGER,            -- Total pages for reading progress
    average_rating NUMERIC(3,2) DEFAULT 0,  -- Precise rating (0.00-5.00)
    review_count INTEGER DEFAULT 0, -- Cached review count
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Performance indexes for books
CREATE INDEX idx_books_titre ON books(titre);
CREATE INDEX idx_books_isbn ON books(isbn);
CREATE INDEX idx_books_publication ON books(date_publication);
CREATE INDEX idx_books_langue ON books(langue);

-- Full-text search index
CREATE INDEX idx_books_titre_gin ON books USING gin(to_tsvector('english', titre));
CREATE INDEX idx_books_description_gin ON books USING gin(to_tsvector('english', description));

-- Array search indexes for denormalized fields
CREATE INDEX idx_books_authors_gin ON books USING gin(author_names);
CREATE INDEX idx_books_genres_gin ON books USING gin(genre_names);

-- Sorting and filtering indexes
CREATE INDEX idx_books_rating ON books(average_rating DESC);
CREATE INDEX idx_books_review_count ON books(review_count DESC);

-- ============================================
-- 5. REVIEWS TABLE
-- ============================================
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(200),
    content TEXT,
    is_flagged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Legacy fields for backward compatibility
    livre_id INTEGER REFERENCES books(id) ON DELETE CASCADE,
    note INTEGER,
    commentaire TEXT,
    nom_utilisateur VARCHAR(100),
    
    -- Constraint: One review per user per book
    UNIQUE(user_id, book_id)
);

-- Indexes for reviews
CREATE INDEX idx_reviews_user ON reviews(user_id);
CREATE INDEX idx_reviews_book ON reviews(book_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_reviews_created ON reviews(created_at DESC);
CREATE INDEX idx_reviews_flagged ON reviews(is_flagged);

-- ============================================
-- 6. READING PROGRESS TABLE
-- ============================================
CREATE TABLE reading_progress (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    current_page INTEGER DEFAULT 1,
    total_pages INTEGER,
    progress_percentage FLOAT DEFAULT 0.0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    last_read_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    
    PRIMARY KEY (user_id, book_id)
);

-- Indexes for reading progress
CREATE INDEX idx_reading_progress_user ON reading_progress(user_id);
CREATE INDEX idx_reading_progress_book ON reading_progress(book_id);
CREATE INDEX idx_reading_progress_last_read ON reading_progress(last_read_at DESC);
CREATE INDEX idx_reading_progress_percentage ON reading_progress(progress_percentage);

-- ============================================
-- 7. MANY-TO-MANY: BOOKS AND AUTHORS
-- ============================================
CREATE TABLE book_author (
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, author_id)
);

-- Indexes for book_author
CREATE INDEX idx_book_author_book ON book_author(book_id);
CREATE INDEX idx_book_author_author ON book_author(author_id);

-- ============================================
-- 8. MANY-TO-MANY: BOOKS AND GENRES
-- ============================================
CREATE TABLE book_genre (
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    genre_id INTEGER NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, genre_id)
);

-- Indexes for book_genre
CREATE INDEX idx_book_genre_book ON book_genre(book_id);
CREATE INDEX idx_book_genre_genre ON book_genre(genre_id);

-- ============================================
-- 9. MANY-TO-MANY: USER FAVORITES
-- ============================================
CREATE TABLE user_favorites (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, book_id)
);

-- Indexes for user_favorites
CREATE INDEX idx_user_favorites_user ON user_favorites(user_id);
CREATE INDEX idx_user_favorites_book ON user_favorites(book_id);
CREATE INDEX idx_user_favorites_added ON user_favorites(added_at DESC);

-- ============================================
-- 10. BOOK PAGES TABLE (Content Storage)
-- ============================================
CREATE TABLE book_pages (
    id SERIAL PRIMARY KEY,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    page_number INTEGER NOT NULL,
    content TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_book_page UNIQUE(book_id, page_number)
);

-- Indexes for book_pages
CREATE INDEX idx_book_pages_book_id ON book_pages(book_id);
CREATE INDEX idx_book_pages_book_page ON book_pages(book_id, page_number);

-- Full-text search index on content
CREATE INDEX idx_book_pages_content_search ON book_pages USING gin(to_tsvector('english', content));

-- ============================================
-- TRIGGERS AND FUNCTIONS
-- ============================================

-- Function to update book rating statistics
CREATE OR REPLACE FUNCTION update_book_rating_stats()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE books
    SET 
        average_rating = (
            SELECT COALESCE(AVG(rating), 0)
            FROM reviews
            WHERE book_id = NEW.book_id
        ),
        review_count = (
            SELECT COUNT(*)
            FROM reviews
            WHERE book_id = NEW.book_id
        ),
        note_moyenne = (
            SELECT COALESCE(AVG(rating), 0)
            FROM reviews
            WHERE book_id = NEW.book_id
        ),
        nombre_reviews = (
            SELECT COUNT(*)
            FROM reviews
            WHERE book_id = NEW.book_id
        ),
        updated_at = NOW()
    WHERE id = NEW.book_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update book ratings when review is added/updated
CREATE TRIGGER trigger_update_book_rating_on_insert
AFTER INSERT ON reviews
FOR EACH ROW
EXECUTE FUNCTION update_book_rating_stats();

CREATE TRIGGER trigger_update_book_rating_on_update
AFTER UPDATE ON reviews
FOR EACH ROW
EXECUTE FUNCTION update_book_rating_stats();

-- Function to update book rating when review is deleted
CREATE OR REPLACE FUNCTION update_book_rating_on_delete()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE books
    SET 
        average_rating = (
            SELECT COALESCE(AVG(rating), 0)
            FROM reviews
            WHERE book_id = OLD.book_id
        ),
        review_count = (
            SELECT COUNT(*)
            FROM reviews
            WHERE book_id = OLD.book_id
        ),
        note_moyenne = (
            SELECT COALESCE(AVG(rating), 0)
            FROM reviews
            WHERE book_id = OLD.book_id
        ),
        nombre_reviews = (
            SELECT COUNT(*)
            FROM reviews
            WHERE book_id = OLD.book_id
        ),
        updated_at = NOW()
    WHERE id = OLD.book_id;
    
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Trigger for review deletion
CREATE TRIGGER trigger_update_book_rating_on_delete
AFTER DELETE ON reviews
FOR EACH ROW
EXECUTE FUNCTION update_book_rating_on_delete();

-- Function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at columns
CREATE TRIGGER trigger_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_books_updated_at
BEFORE UPDATE ON books
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_reviews_updated_at
BEFORE UPDATE ON reviews
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trigger_reading_progress_updated_at
BEFORE UPDATE ON reading_progress
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- View: Books with full details
CREATE OR REPLACE VIEW v_books_full AS
SELECT 
    b.id,
    b.titre,
    b.isbn,
    b.date_publication,
    b.description,
    b.image_url,
    b.nombre_pages,
    b.total_pages,
    b.langue,
    b.editeur,
    b.average_rating,
    b.review_count,
    b.author_names,
    b.genre_names,
    b.word_count,
    b.content_path,
    b.created_at,
    b.updated_at,
    COALESCE(ARRAY_AGG(DISTINCT a.nom || ' ' || COALESCE(a.prenom, '')) FILTER (WHERE a.id IS NOT NULL), '{}') as author_full_names,
    COALESCE(ARRAY_AGG(DISTINCT g.nom) FILTER (WHERE g.id IS NOT NULL), '{}') as genre_full_names
FROM books b
LEFT JOIN book_author ba ON b.id = ba.book_id
LEFT JOIN authors a ON ba.author_id = a.id
LEFT JOIN book_genre bg ON b.id = bg.book_id
LEFT JOIN genres g ON bg.genre_id = g.id
GROUP BY b.id;

-- View: User reading statistics
CREATE OR REPLACE VIEW v_user_reading_stats AS
SELECT 
    u.id as user_id,
    u.email,
    u.first_name,
    u.last_name,
    COUNT(DISTINCT rp.book_id) as books_started,
    COUNT(DISTINCT CASE WHEN rp.progress_percentage >= 100 THEN rp.book_id END) as books_finished,
    COUNT(DISTINCT uf.book_id) as favorites_count,
    COUNT(DISTINCT r.id) as reviews_count,
    COALESCE(AVG(r.rating), 0) as avg_rating_given,
    COALESCE(AVG(rp.progress_percentage), 0) as avg_progress
FROM users u
LEFT JOIN reading_progress rp ON u.id = rp.user_id
LEFT JOIN user_favorites uf ON u.id = uf.user_id
LEFT JOIN reviews r ON u.id = r.user_id
GROUP BY u.id, u.email, u.first_name, u.last_name;

-- View: Book statistics
CREATE OR REPLACE VIEW v_book_stats AS
SELECT 
    b.id as book_id,
    b.titre,
    b.isbn,
    b.average_rating,
    b.review_count,
    COUNT(DISTINCT uf.user_id) as favorites_count,
    COUNT(DISTINCT rp.user_id) as readers_count,
    COUNT(DISTINCT CASE WHEN rp.progress_percentage >= 100 THEN rp.user_id END) as finished_count
FROM books b
LEFT JOIN user_favorites uf ON b.id = uf.book_id
LEFT JOIN reading_progress rp ON b.id = rp.book_id
GROUP BY b.id, b.titre, b.isbn, b.average_rating, b.review_count;

-- ============================================
-- SAMPLE DATA QUERIES
-- ============================================

-- Get top rated books
-- SELECT * FROM books WHERE review_count >= 5 ORDER BY average_rating DESC LIMIT 10;

-- Get books by genre
-- SELECT * FROM books WHERE 'Fiction' = ANY(genre_names);

-- Get books by author
-- SELECT * FROM books WHERE 'John Doe' = ANY(author_names);

-- Get user's reading progress
-- SELECT * FROM reading_progress WHERE user_id = 1 ORDER BY last_read_at DESC;

-- Get user's favorites
-- SELECT b.* FROM books b
-- JOIN user_favorites uf ON b.id = uf.book_id
-- WHERE uf.user_id = 1
-- ORDER BY uf.added_at DESC;

-- Get book reviews with user info
-- SELECT r.*, u.first_name, u.last_name
-- FROM reviews r
-- JOIN users u ON r.user_id = u.id
-- WHERE r.book_id = 1
-- ORDER BY r.created_at DESC;

-- ============================================
-- PERFORMANCE OPTIMIZATION QUERIES
-- ============================================

-- Analyze table statistics
-- ANALYZE users;
-- ANALYZE books;
-- ANALYZE reviews;
-- ANALYZE reading_progress;

-- Vacuum tables
-- VACUUM ANALYZE users;
-- VACUUM ANALYZE books;
-- VACUUM ANALYZE reviews;

-- Check index usage
-- SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
-- FROM pg_stat_user_indexes
-- ORDER BY idx_scan DESC;

-- ============================================
-- END OF SCHEMA
-- ============================================
