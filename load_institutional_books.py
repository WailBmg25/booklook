#!/usr/bin/env python3
"""
BookLook Enhanced Data Loader for Institutional Books Dataset

This script loads books from HuggingFace institutional/institutional-books-1.0 dataset with:
- Streaming: Memory-efficient chunked loading (100 books per batch)
- ISBN Lookup: Google Books API + Open Library + isbnlib fallback
- Cover Images: Multiple sources with fallbacks
- Authentication: HuggingFace token support

Dataset Columns (from institutional/institutional-books-1.0):
- barcode_src: Unique identifier for the book
- title_src: Book title
- author_src: Author name(s)
- date1_src: Primary publication date
- date2_src: Secondary date (if applicable)
- page_count_src: Number of pages
- language_src: Language code
- topic_or_subject_src: Subject/topic classification
- genre_or_form_src: Genre classification
- identifiers_src: Contains ISBN, LCCN, OCOLC identifiers
- text_by_page_src: Full text content by page
"""

import os
import random
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import execute_batch
from datasets import load_dataset
from huggingface_hub import login
from dotenv import load_dotenv
import time
import isbnlib

# Load environment variables
load_dotenv('.env.production')

# ============================================================================
# CONFIGURATION
# ============================================================================

# HuggingFace Authentication
HF_TOKEN = os.getenv('HUGGINGFACE_TOKEN', '')
if HF_TOKEN:
    login(token=HF_TOKEN)
    print("✅ Logged in to HuggingFace")
else:
    print("⚠️  No HuggingFace token - proceeding without authentication")

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'book_library'),
    'user': os.getenv('DB_USER', 'bookuser'),
    'password': os.getenv('DB_PASSWORD', 'bookpass123')
}

# Dataset configuration
DATASET_NAME = "institutional/institutional-books-1.0"
CHUNK_SIZE = 100  # Load 100 books at a time
MAX_CHUNKS = 10  # Set to None for all books, or number for testing (10 = 1000 books)

# API rate limiting
API_DELAY = 0.5  # Seconds between API calls
GOOGLE_BOOKS_API_KEY = os.getenv('GOOGLE_BOOKS_API_KEY', '')  # Optional

print(f"\n📚 Dataset: {DATASET_NAME}")
print(f"📦 Chunk size: {CHUNK_SIZE} books per batch")
print(f"🔌 Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}\n")

# ============================================================================
# DATASET COLUMN DESCRIPTIONS
# ============================================================================

DATASET_COLUMNS = {
    'barcode_src': 'Unique barcode identifier from source library',
    'title_src': 'Book title from source metadata',
    'author_src': 'Author name(s) from source metadata',
    'date1_src': 'Primary publication date',
    'date2_src': 'Secondary date (reprint, edition, etc.)',
    'date_types_src': 'Type of dates provided',
    'page_count_src': 'Number of pages in the book',
    'token_count_o200k_base_gen': 'Token count using o200k_base tokenizer',
    'language_src': 'Language code from source',
    'language_gen': 'Generated/detected language',
    'language_distribution_gen': 'Language distribution analysis',
    'topic_or_subject_src': 'Subject classification from source',
    'topic_or_subject_gen': 'Generated topic classification',
    'genre_or_form_src': 'Genre classification from source',
    'general_note_src': 'General notes about the book',
    'ocr_score_src': 'OCR quality score from source',
    'ocr_score_gen': 'Generated OCR quality score',
    'identifiers_src': 'Contains ISBN, LCCN, OCOLC identifiers',
    'text_by_page_src': 'Full text content by page (original OCR)',
    'text_by_page_gen': 'Full text content by page (cleaned/generated)',
    'text_analysis_gen': 'Text analysis statistics',
    'hathitrust_data_ext': 'HathiTrust metadata and links'
}

print("📋 DATASET COLUMN DESCRIPTIONS:")
print("=" * 80)
for col, desc in DATASET_COLUMNS.items():
    print(f"  • {col:35} : {desc}")
print("=" * 80 + "\n")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def extract_isbn_from_identifiers(identifiers: Dict) -> Optional[str]:
    """Extract ISBN from identifiers_src field."""
    if not identifiers:
        return None
    
    isbn_list = identifiers.get('isbn', [])
    if isbn_list and len(isbn_list) > 0:
        # Return first valid ISBN
        for isbn in isbn_list:
            if isbn and len(isbn) >= 10:
                return isbn.strip()
    return None


def lookup_isbn_google_books(title: str, author: str) -> Optional[str]:
    """Lookup ISBN using Google Books API."""
    try:
        query = f"{title} {author}".strip()
        url = "https://www.googleapis.com/books/v1/volumes"
        params = {'q': query, 'maxResults': 1}
        
        if GOOGLE_BOOKS_API_KEY:
            params['key'] = GOOGLE_BOOKS_API_KEY
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if 'items' in data and len(data['items']) > 0:
                volume_info = data['items'][0].get('volumeInfo', {})
                identifiers = volume_info.get('industryIdentifiers', [])
                
                for identifier in identifiers:
                    if identifier.get('type') in ['ISBN_13', 'ISBN_10']:
                        return identifier.get('identifier')
    except Exception as e:
        pass
    
    return None


def lookup_isbn_openlibrary(title: str, author: str) -> Optional[str]:
    """Lookup ISBN using Open Library API."""
    try:
        query = f"{title} {author}".strip()
        url = f"https://openlibrary.org/search.json"
        params = {'q': query, 'limit': 1}
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if 'docs' in data and len(data['docs']) > 0:
                doc = data['docs'][0]
                isbn_list = doc.get('isbn', [])
                if isbn_list:
                    return isbn_list[0]
    except Exception as e:
        pass
    
    return None


def get_isbn_for_book(title: str, author: str, identifiers: Dict) -> Optional[str]:
    """
    Get ISBN for a book using multiple strategies:
    1. Extract from dataset identifiers
    2. Google Books API lookup
    3. Open Library API lookup
    """
    # Strategy 1: Extract from dataset
    isbn = extract_isbn_from_identifiers(identifiers)
    if isbn:
        return isbn
    
    # Strategy 2: Google Books API
    time.sleep(API_DELAY)
    isbn = lookup_isbn_google_books(title, author)
    if isbn:
        return isbn
    
    # Strategy 3: Open Library API
    time.sleep(API_DELAY)
    isbn = lookup_isbn_openlibrary(title, author)
    if isbn:
        return isbn
    
    return None


def get_cover_image_url(title: str, author: str, isbn: Optional[str]) -> str:
    """
    Get book cover image URL using multiple sources:
    1. Open Library Covers API (if ISBN available)
    2. Google Books API
    3. Placeholder fallback
    """
    # Strategy 1: Open Library Covers (best quality if ISBN available)
    if isbn:
        # Try ISBN-13 first, then ISBN-10
        cover_url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
        try:
            response = requests.head(cover_url, timeout=3)
            if response.status_code == 200:
                return cover_url
        except:
            pass
    
    # Strategy 2: Open Library Search
    try:
        query = f"{title} {author}".strip()
        url = f"https://openlibrary.org/search.json"
        params = {'q': query, 'limit': 1}
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if 'docs' in data and len(data['docs']) > 0:
                doc = data['docs'][0]
                if 'cover_i' in doc:
                    cover_id = doc['cover_i']
                    return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
    except:
        pass
    
    # Strategy 3: Placeholder
    title_short = title[:30].replace(' ', '+')
    return f"https://via.placeholder.com/400x600/4A5568/FFFFFF?text={title_short}"


def infer_genres(title: str, author: str, subject: str, genre: str) -> List[str]:
    """Infer genres based on title, author, subject, and genre fields."""
    GENRE_KEYWORDS = {
        'Fiction': ['novel', 'story', 'fiction', 'tale', 'narrative'],
        'Science': ['science', 'physics', 'chemistry', 'biology', 'mathematics', 'astronomy'],
        'History': ['history', 'historical', 'war', 'ancient', 'medieval'],
        'Philosophy': ['philosophy', 'philosophical', 'ethics', 'logic', 'metaphysics'],
        'Poetry': ['poetry', 'poems', 'verse', 'sonnet'],
        'Drama': ['drama', 'play', 'theatre', 'tragedy', 'comedy'],
        'Biography': ['biography', 'autobiography', 'memoir', 'life'],
        'Religion': ['religion', 'religious', 'theology', 'spiritual', 'bible', 'god'],
        'Travel': ['travel', 'journey', 'voyage', 'adventure', 'exploration'],
        'Art': ['art', 'painting', 'sculpture', 'architecture', 'music'],
    }
    
    text = f"{title} {author} {subject} {genre}".lower()
    matched_genres = []
    
    for genre_name, keywords in GENRE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            matched_genres.append(genre_name)
    
    # Default if none matched
    if not matched_genres:
        matched_genres = ['Literature']
    
    return matched_genres[:2]  # Max 2 genres


def generate_description(title: str, author: str, subject: str, page_count: int) -> str:
    """Generate a book description from available metadata."""
    if subject and subject.strip():
        return f"'{title}' by {author} is a {page_count}-page work exploring {subject.lower()}."
    else:
        return f"'{title}' by {author} is a {page_count}-page literary work."


def generate_reviews(book_title: str, num_reviews: int = 3) -> List[Dict]:
    """Generate sample reviews for a book."""
    reviews = []
    review_templates = [
        "An excellent read that provides great insights.",
        "A classic work that stands the test of time.",
        "Highly recommended for anyone interested in the subject.",
        "A comprehensive and well-written book.",
        "An important contribution to the field."
    ]
    
    for _ in range(num_reviews):
        rating = random.randint(3, 5)
        review_text = random.choice(review_templates)
        created_at = datetime.now() - timedelta(days=random.randint(1, 365))
        
        reviews.append({
            'rating': rating,
            'review_text': review_text,
            'created_at': created_at
        })
    
    return reviews


# ============================================================================
# DATA LOADING FUNCTIONS
# ============================================================================

def process_book_chunk(chunk: List[Dict], demo_user_id: int, conn, cur, 
                       genre_cache: Dict, author_cache: Dict) -> int:
    """Process a chunk of books and load to database."""
    loaded_count = 0
    
    for i, book in enumerate(chunk):
        try:
            # Extract basic info
            title = book.get('title_src', f'Unknown Title')
            author = book.get('author_src', 'Unknown Author')
            
            if not title or not author:
                continue
            
            # Clean author name
            if not author or author.strip() == '':
                author = 'Anonymous'
            
            # Extract identifiers
            identifiers = book.get('identifiers_src', {})
            
            # Get ISBN (with API lookups)
            isbn = get_isbn_for_book(title, author, identifiers)
            
            # Get cover image
            cover_url = get_cover_image_url(title, author, isbn)
            
            # Extract other metadata
            date_pub = book.get('date1_src', '1900-01-01')
            page_count = book.get('page_count_src', 0)
            subject = book.get('topic_or_subject_src', '')
            genre_src = book.get('genre_or_form_src', '')
            
            # Infer genres
            genres = infer_genres(title, author, subject, genre_src)
            
            # Generate description
            description = generate_description(title, author, subject, page_count)
            
            # Generate reviews
            reviews = generate_reviews(title, num_reviews=3)
            
            # Insert book
            cur.execute("""
                INSERT INTO books (titre, isbn, date_publication, description, image_url)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (titre) DO NOTHING
                RETURNING id
            """, (title, isbn, date_pub, description, cover_url))
            
            result = cur.fetchone()
            if not result:
                continue  # Book already exists
            
            book_id = result[0]
            
            # Insert or get author
            if author not in author_cache:
                cur.execute("""
                    INSERT INTO authors (nom, prenom)
                    VALUES (%s, %s)
                    ON CONFLICT (nom, prenom) DO UPDATE SET nom = EXCLUDED.nom
                    RETURNING id
                """, (author, ''))
                author_cache[author] = cur.fetchone()[0]
            
            author_id = author_cache[author]
            
            # Link book to author
            cur.execute("""
                INSERT INTO book_authors (book_id, author_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
            """, (book_id, author_id))
            
            # Insert genres and link to book
            for genre_name in genres:
                if genre_name not in genre_cache:
                    cur.execute("""
                        INSERT INTO genres (nom)
                        VALUES (%s)
                        ON CONFLICT (nom) DO UPDATE SET nom = EXCLUDED.nom
                        RETURNING id
                    """, (genre_name,))
                    genre_cache[genre_name] = cur.fetchone()[0]
                
                genre_id = genre_cache[genre_name]
                
                cur.execute("""
                    INSERT INTO book_genres (book_id, genre_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """, (book_id, genre_id))
            
            # Insert reviews
            for review in reviews:
                cur.execute("""
                    INSERT INTO reviews (book_id, user_id, rating, review_text, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    book_id,
                    demo_user_id,
                    review['rating'],
                    review['review_text'],
                    review['created_at']
                ))
            
            loaded_count += 1
            
        except Exception as e:
            print(f"  ⚠️  Error loading book '{book.get('title_src', 'Unknown')}': {e}")
            conn.rollback()
            continue
    
    conn.commit()
    return loaded_count


def main():
    """Main execution function."""
    print("=" * 80)
    print("📥 LOADING INSTITUTIONAL BOOKS DATASET")
    print("=" * 80 + "\n")
    
    # Load dataset in streaming mode
    print(f"📥 Loading dataset stream: {DATASET_NAME}...\n")
    dataset_stream = load_dataset(DATASET_NAME, split="train", streaming=True)
    
    # Connect to database
    print("🔌 Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("✅ Connected to PostgreSQL database\n")
    
    # Create demo user
    cur.execute("""
        INSERT INTO users (email, password_hash, first_name, last_name, is_admin)
        VALUES ('demo@booklook.com', 'hashed_password', 'Demo', 'User', false)
        ON CONFLICT (email) DO NOTHING
        RETURNING id
    """)
    result = cur.fetchone()
    if result:
        demo_user_id = result[0]
    else:
        cur.execute("SELECT id FROM users WHERE email = 'demo@booklook.com'")
        demo_user_id = cur.fetchone()[0]
    
    conn.commit()
    print(f"👤 Demo user ID: {demo_user_id}\n")
    
    # Initialize caches
    genre_cache = {}
    author_cache = {}
    
    # Process in chunks
    total_loaded = 0
    chunk_num = 0
    chunk = []
    
    print(f"📦 Processing books in chunks of {CHUNK_SIZE}...\n")
    
    for book in dataset_stream:
        chunk.append(book)
        
        if len(chunk) >= CHUNK_SIZE:
            chunk_num += 1
            print(f"📚 Processing chunk {chunk_num} ({len(chunk)} books)...")
            
            loaded = process_book_chunk(chunk, demo_user_id, conn, cur, genre_cache, author_cache)
            total_loaded += loaded
            
            print(f"   ✅ Loaded {loaded} books (Total: {total_loaded})\n")
            
            chunk = []
            
            # Check if we've reached max chunks
            if MAX_CHUNKS and chunk_num >= MAX_CHUNKS:
                print(f"🛑 Reached maximum chunks limit ({MAX_CHUNKS})\n")
                break
    
    # Process remaining books
    if chunk:
        chunk_num += 1
        print(f"📚 Processing final chunk {chunk_num} ({len(chunk)} books)...")
        loaded = process_book_chunk(chunk, demo_user_id, conn, cur, genre_cache, author_cache)
        total_loaded += loaded
        print(f"   ✅ Loaded {loaded} books (Total: {total_loaded})\n")
    
    # Verification
    print("=" * 80)
    print("🔍 VERIFICATION")
    print("=" * 80 + "\n")
    
    cur.execute("SELECT COUNT(*) FROM books")
    book_count = cur.fetchone()[0]
    print(f"📚 Total books in database: {book_count}")
    
    cur.execute("SELECT COUNT(*) FROM authors")
    author_count = cur.fetchone()[0]
    print(f"✍️  Total authors: {author_count}")
    
    cur.execute("SELECT COUNT(*) FROM genres")
    genre_count = cur.fetchone()[0]
    print(f"🏷️  Total genres: {genre_count}")
    
    cur.execute("SELECT COUNT(*) FROM reviews")
    review_count = cur.fetchone()[0]
    print(f"⭐ Total reviews: {review_count}")
    
    # Sample books with covers
    cur.execute("""
        SELECT titre, isbn, image_url 
        FROM books 
        WHERE image_url IS NOT NULL 
        ORDER BY id DESC
        LIMIT 5
    """)
    print("\n📸 Sample recently loaded books:")
    for title, isbn, url in cur.fetchall():
        isbn_display = isbn if isbn else "No ISBN"
        print(f"  • {title[:60]}...")
        print(f"    ISBN: {isbn_display}")
        print(f"    Cover: {url[:80]}...")
    
    # Cleanup
    cur.close()
    conn.close()
    print("\n✅ Database connection closed")
    print("\n🎉 All done! Your database is now populated with enriched book data!")
    print("=" * 80)


if __name__ == "__main__":
    main()
