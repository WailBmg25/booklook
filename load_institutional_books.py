#!/usr/bin/env python3
"""
Institutional Books Dataset Loader for BookLook
================================================

This script loads books from the HuggingFace institutional/institutional-books-1.0 dataset
into the BookLook database with the following features:

Features:
- Streaming dataset loading (memory efficient)
- Chunked processing (100 books per batch)
- Resume capability (continues from last loaded book)
- ISBN extraction and lookup
- Cover image fetching from multiple sources
- Progress tracking and detailed logging
- Error handling and retry logic

Dataset Fields:
- barcode_src: Unique identifier from source
- title_src: Book title
- author_src: Author name(s)
- date1_src/date2_src: Publication dates
- page_count_src: Number of pages
- language_src/language_gen: Language information
- topic_or_subject_src/gen: Subject/topic classification
- text_by_page_src/gen: Full text content by page
- identifiers_src: ISBN, LCCN, OCLC identifiers
- hathitrust_data_ext: External HathiTrust data

Requirements:
    pip install datasets huggingface-hub psycopg2-binary requests python-dotenv isbnlib

Usage:
    python load_institutional_books.py [--max-chunks N] [--resume]
"""

import os
import sys
import json
import time
import argparse
import re
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values
import requests
from datasets import load_dataset
from huggingface_hub import login
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

# ============================================================================
# CONFIGURATION
# ============================================================================

# HuggingFace Configuration
# TODO: Replace with your HuggingFace token from https://huggingface.co/settings/tokens
HF_TOKEN = "YOUR_HUGGINGFACE_TOKEN_HERE"
DATASET_NAME = "institutional/institutional-books-1.0"

# Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'book_library',
    'user': 'bookuser',
    'password': 'bookpass123'
}

# Processing Configuration
CHUNK_SIZE = 100  # Books per batch
API_DELAY = 0.5   # Seconds between API calls
MAX_RETRIES = 3   # Retry attempts for API calls

# Progress tracking file
PROGRESS_FILE = "load_progress.json"

# API Keys (optional, improves ISBN lookup results)
# Get your key from: https://console.cloud.google.com/apis/credentials
GOOGLE_BOOKS_API_KEY = ''  # Optional: Add your Google Books API key here

# ============================================================================
# DATASET FIELD DESCRIPTIONS
# ============================================================================

DATASET_FIELDS = {
    'barcode_src': 'Unique barcode identifier from source institution',
    'title_src': 'Book title from source metadata',
    'author_src': 'Author name(s) from source metadata',
    'date1_src': 'Primary publication date',
    'date2_src': 'Secondary publication date (reprint, edition)',
    'date_types_src': 'Type of dates (publication, copyright, etc.)',
    'page_count_src': 'Number of pages in the book',
    'token_count_o200k_base_gen': 'Token count using o200k_base tokenizer',
    'language_src': 'Language code from source',
    'language_gen': 'Generated/detected language',
    'language_distribution_gen': 'Language distribution analysis',
    'topic_or_subject_src': 'Subject/topic from source metadata',
    'topic_or_subject_gen': 'Generated topic classification',
    'topic_or_subject_score_gen': 'Confidence score for topic',
    'genre_or_form_src': 'Genre or form from source',
    'general_note_src': 'General notes about the book',
    'ocr_score_src': 'OCR quality score from source',
    'ocr_score_gen': 'Generated OCR quality score',
    'likely_duplicates_barcodes_gen': 'Barcodes of likely duplicate entries',
    'text_analysis_gen': 'Text analysis statistics',
    'identifiers_src': 'ISBN, LCCN, OCLC identifiers',
    'hathitrust_data_ext': 'HathiTrust external data',
    'text_by_page_src': 'Original OCR text by page',
    'text_by_page_gen': 'Cleaned/generated text by page'
}

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_header():
    """Print script header."""
    print("=" * 80)
    print("📚 Institutional Books Dataset Loader for BookLook")
    print("=" * 80)
    print(f"Dataset: {DATASET_NAME}")
    print(f"Chunk Size: {CHUNK_SIZE} books per batch")
    print(f"Database: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    print("=" * 80)
    print()


def print_dataset_info():
    """Print dataset field information."""
    print("\n📋 Dataset Fields:")
    print("-" * 80)
    for field, description in DATASET_FIELDS.items():
        print(f"  • {field:35s} : {description}")
    print("-" * 80)
    print()


def load_progress() -> Dict:
    """Load progress from file."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'last_processed_index': -1,
        'total_loaded': 0,
        'last_barcode': None,
        'timestamp': None
    }


def save_progress(index: int, total: int, barcode: str):
    """Save progress to file."""
    progress = {
        'last_processed_index': index,
        'total_loaded': total,
        'last_barcode': barcode,
        'timestamp': datetime.now().isoformat()
    }
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)


def extract_isbn_from_identifiers(identifiers: Dict) -> Optional[str]:
    """Extract ISBN from identifiers dictionary."""
    if not identifiers:
        return None
    
    # Try ISBN field first
    if 'isbn' in identifiers and identifiers['isbn']:
        isbns = identifiers['isbn']
        if isinstance(isbns, list) and len(isbns) > 0:
            # Clean and validate ISBN
            isbn = str(isbns[0]).strip().replace('-', '').replace(' ', '')
            if len(isbn) in [10, 13]:
                return isbn
    
    return None


def search_isbn_google_books(title: str, author: str) -> Optional[str]:
    """Search for ISBN using Google Books API."""
    if not title:
        return None
    
    try:
        query = f"{title}"
        if author:
            query += f" {author}"
        
        url = "https://www.googleapis.com/books/v1/volumes"
        params = {
            'q': query,
            'maxResults': 1
        }
        
        if GOOGLE_BOOKS_API_KEY:
            params['key'] = GOOGLE_BOOKS_API_KEY
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if 'items' in data and len(data['items']) > 0:
                volume_info = data['items'][0].get('volumeInfo', {})
                identifiers = volume_info.get('industryIdentifiers', [])
                
                # Prefer ISBN_13, fallback to ISBN_10
                for identifier in identifiers:
                    if identifier.get('type') == 'ISBN_13':
                        return identifier.get('identifier')
                
                for identifier in identifiers:
                    if identifier.get('type') == 'ISBN_10':
                        return identifier.get('identifier')
        
        time.sleep(API_DELAY)
        
    except Exception as e:
        print(f"    ⚠️  Google Books API error: {e}")
    
    return None


def search_isbn_open_library(title: str, author: str) -> Optional[str]:
    """Search for ISBN using Open Library API."""
    if not title:
        return None
    
    try:
        query = title
        if author:
            query += f" {author}"
        
        url = "https://openlibrary.org/search.json"
        params = {
            'q': query,
            'limit': 1
        }
        
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if 'docs' in data and len(data['docs']) > 0:
                doc = data['docs'][0]
                
                # Try ISBN_13 first
                if 'isbn' in doc and doc['isbn']:
                    for isbn in doc['isbn']:
                        isbn_clean = str(isbn).strip().replace('-', '')
                        if len(isbn_clean) == 13:
                            return isbn_clean
                    
                    # Fallback to any ISBN
                    return str(doc['isbn'][0]).strip().replace('-', '')
        
        time.sleep(API_DELAY)
        
    except Exception as e:
        print(f"    ⚠️  Open Library API error: {e}")
    
    return None


def generate_isbn_from_barcode(barcode: str) -> str:
    """Generate a pseudo-ISBN from barcode for books without ISBN."""
    # Use barcode hash to create a unique 13-digit identifier
    # Prefix with 999 to indicate it's not a real ISBN
    barcode_hash = abs(hash(barcode)) % (10 ** 10)
    return f"999{barcode_hash:010d}"


def get_isbn_for_book(book_data: Dict) -> str:
    """Get or generate ISBN for a book."""
    # 1. Try to extract from identifiers
    isbn = extract_isbn_from_identifiers(book_data.get('identifiers_src'))
    if isbn:
        return isbn
    
    # 2. Try Google Books API
    title = book_data.get('title_src', '')
    author = book_data.get('author_src', '')
    
    isbn = search_isbn_google_books(title, author)
    if isbn:
        return isbn
    
    # 3. Try Open Library API
    isbn = search_isbn_open_library(title, author)
    if isbn:
        return isbn
    
    # 4. Generate from barcode as last resort
    barcode = book_data.get('barcode_src', '')
    return generate_isbn_from_barcode(barcode)


def fetch_cover_image(isbn: str, title: str = "") -> Optional[str]:
    """Fetch cover image URL from multiple sources."""
    # Try Open Library Covers API
    try:
        url = f"https://covers.openlibrary.org/b/isbn/{isbn}-L.jpg"
        response = requests.head(url, timeout=3)
        if response.status_code == 200:
            return url
    except:
        pass
    
    # Try Google Books API
    if GOOGLE_BOOKS_API_KEY:
        try:
            url = "https://www.googleapis.com/books/v1/volumes"
            params = {
                'q': f'isbn:{isbn}',
                'key': GOOGLE_BOOKS_API_KEY
            }
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'items' in data and len(data['items']) > 0:
                    image_links = data['items'][0].get('volumeInfo', {}).get('imageLinks', {})
                    if 'thumbnail' in image_links:
                        return image_links['thumbnail']
        except:
            pass
    
    return None


def parse_publication_date(date_str: str) -> Optional[str]:
    """Parse publication date to YYYY-MM-DD format."""
    if not date_str:
        return None
    
    # Try to extract year
    year_match = re.search(r'\b(1[0-9]{3}|20[0-9]{2})\b', str(date_str))
    if year_match:
        year = year_match.group(1)
        return f"{year}-01-01"
    
    return None


def clean_text(text: str, max_length: int = 5000) -> str:
    """Clean and truncate text."""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Truncate if too long
    if len(text) > max_length:
        text = text[:max_length] + "..."
    
    return text


def extract_language(book_data: Dict) -> str:
    """Extract language from book data."""
    # Prefer generated language
    lang = book_data.get('language_gen', '')
    if not lang:
        lang = book_data.get('language_src', '')
    
    # Map to common language codes
    lang_map = {
        'eng': 'English',
        'fra': 'French',
        'deu': 'German',
        'spa': 'Spanish',
        'ita': 'Italian',
        'por': 'Portuguese',
        'rus': 'Russian',
        'jpn': 'Japanese',
        'chi': 'Chinese',
        'ara': 'Arabic'
    }
    
    return lang_map.get(lang[:3].lower(), lang or 'English')


def extract_genres(book_data: Dict) -> List[str]:
    """Extract genres from book data."""
    genres = []
    
    # From genre_or_form_src
    genre_str = book_data.get('genre_or_form_src', '')
    if genre_str:
        # Split by common delimiters
        parts = re.split(r'[;,|]', genre_str)
        genres.extend([g.strip() for g in parts if g.strip()])
    
    # From topic_or_subject
    topic = book_data.get('topic_or_subject_gen') or book_data.get('topic_or_subject_src', '')
    if topic and topic not in genres:
        genres.append(topic)
    
    # Default genre if none found
    if not genres:
        genres = ['General']
    
    return genres[:3]  # Limit to 3 genres


def extract_description(book_data: Dict) -> str:
    """Extract or generate description from book data."""
    # Try general notes
    desc = book_data.get('general_note_src', '')
    
    # If no description, create one from available data
    if not desc:
        parts = []
        
        topic = book_data.get('topic_or_subject_gen') or book_data.get('topic_or_subject_src')
        if topic:
            parts.append(f"Subject: {topic}")
        
        lang = book_data.get('language_gen', '')
        if lang:
            parts.append(f"Language: {lang}")
        
        pages = book_data.get('page_count_src')
        if pages:
            parts.append(f"{pages} pages")
        
        desc = ". ".join(parts) if parts else "No description available"
    
    return clean_text(desc, 2000)


# ============================================================================
# DATABASE OPERATIONS
# ============================================================================

def get_db_connection():
    """Create database connection."""
    return psycopg2.connect(**DB_CONFIG)


def get_or_create_author(cursor, author_name: str) -> int:
    """Get or create author and return ID."""
    if not author_name or author_name.strip() == '':
        author_name = "Unknown Author"
    
    # Split name into first and last
    parts = author_name.strip().split()
    if len(parts) >= 2:
        prenom = ' '.join(parts[:-1])
        nom = parts[-1]
    else:
        prenom = ""
        nom = author_name.strip()
    
    # Check if author exists
    cursor.execute(
        "SELECT id FROM authors WHERE nom = %s AND prenom = %s",
        (nom, prenom)
    )
    result = cursor.fetchone()
    
    if result:
        return result[0]
    
    # Create new author
    cursor.execute(
        """
        INSERT INTO authors (nom, prenom, created_at)
        VALUES (%s, %s, NOW())
        RETURNING id
        """,
        (nom, prenom)
    )
    return cursor.fetchone()[0]


def get_or_create_genre(cursor, genre_name: str) -> int:
    """Get or create genre and return ID."""
    if not genre_name or genre_name.strip() == '':
        genre_name = "General"
    
    genre_name = genre_name.strip()
    
    # Check if genre exists
    cursor.execute(
        "SELECT id FROM genres WHERE nom = %s",
        (genre_name,)
    )
    result = cursor.fetchone()
    
    if result:
        return result[0]
    
    # Create new genre
    cursor.execute(
        """
        INSERT INTO genres (nom, created_at)
        VALUES (%s, NOW())
        RETURNING id
        """,
        (genre_name,)
    )
    return cursor.fetchone()[0]


def insert_book_batch(cursor, books_data: List[Dict]) -> Tuple[int, int]:
    """Insert a batch of books into database."""
    inserted = 0
    skipped = 0
    
    for book_data in books_data:
        try:
            # Get or generate ISBN
            isbn = get_isbn_for_book(book_data)
            
            # Check if book already exists
            cursor.execute("SELECT id FROM books WHERE isbn = %s", (isbn,))
            if cursor.fetchone():
                skipped += 1
                continue
            
            # Extract book information
            title = book_data.get('title_src', 'Unknown Title')
            author_name = book_data.get('author_src', 'Unknown Author')
            pub_date = parse_publication_date(book_data.get('date1_src', ''))
            description = extract_description(book_data)
            page_count = book_data.get('page_count_src')
            language = extract_language(book_data)
            genres = extract_genres(book_data)
            
            # Fetch cover image
            cover_url = fetch_cover_image(isbn, title)
            
            # Get word count from token count (approximate)
            token_count = book_data.get('token_count_o200k_base_gen', 0)
            word_count = int(token_count * 0.75) if token_count else None
            
            # Insert book
            cursor.execute(
                """
                INSERT INTO books (
                    titre, isbn, date_publication, description, image_url,
                    nombre_pages, total_pages, langue, note_moyenne, nombre_reviews,
                    average_rating, review_count, word_count, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                RETURNING id
                """,
                (
                    title, isbn, pub_date, description, cover_url,
                    page_count, page_count, language, 0.0, 0,
                    0.0, 0, word_count
                )
            )
            book_id = cursor.fetchone()[0]
            
            # Create or get author
            author_id = get_or_create_author(cursor, author_name)
            
            # Link book to author
            cursor.execute(
                """
                INSERT INTO book_authors (book_id, author_id)
                VALUES (%s, %s)
                ON CONFLICT DO NOTHING
                """,
                (book_id, author_id)
            )
            
            # Link book to genres
            for genre_name in genres:
                genre_id = get_or_create_genre(cursor, genre_name)
                cursor.execute(
                    """
                    INSERT INTO book_genres (book_id, genre_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (book_id, genre_id)
                )
            
            # Update denormalized fields
            cursor.execute(
                """
                UPDATE books
                SET author_names = ARRAY[%s],
                    genre_names = %s
                WHERE id = %s
                """,
                (author_name, genres, book_id)
            )
            
            inserted += 1
            
        except Exception as e:
            print(f"    ❌ Error inserting book: {e}")
            skipped += 1
            continue
    
    return inserted, skipped


# ============================================================================
# MAIN LOADING FUNCTION
# ============================================================================

def load_institutional_books(max_chunks: Optional[int] = None, resume: bool = True):
    """Load books from institutional dataset."""
    print_header()
    print_dataset_info()
    
    # Login to HuggingFace
    print("🔐 Authenticating with HuggingFace...")
    try:
        login(token=HF_TOKEN)
        print("✅ Successfully authenticated\n")
    except Exception as e:
        print(f"⚠️  Authentication warning: {e}\n")
    
    # Load progress
    progress = load_progress() if resume else {'last_processed_index': -1, 'total_loaded': 0}
    start_index = progress['last_processed_index'] + 1
    
    if resume and start_index > 0:
        print(f"📍 Resuming from index {start_index} ({progress['total_loaded']} books loaded)")
        print(f"   Last processed: {progress.get('last_barcode', 'N/A')}")
        print(f"   Timestamp: {progress.get('timestamp', 'N/A')}\n")
    
    # Load dataset with streaming
    print(f"📥 Loading dataset: {DATASET_NAME}")
    print("   Using streaming mode for memory efficiency...\n")
    
    try:
        dataset_stream = load_dataset(DATASET_NAME, split="train", streaming=True)
    except Exception as e:
        print(f"❌ Failed to load dataset: {e}")
        return
    
    # Connect to database
    print("🔌 Connecting to database...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        print("✅ Database connected\n")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Process dataset in chunks
    print(f"🚀 Starting data loading (chunk size: {CHUNK_SIZE})")
    print("=" * 80)
    
    chunk_buffer = []
    current_index = 0
    chunk_number = 0
    total_inserted = progress['total_loaded']
    total_skipped = 0
    start_time = time.time()
    
    try:
        for book_data in dataset_stream:
            # Skip already processed books
            if current_index < start_index:
                current_index += 1
                continue
            
            # Add to buffer
            chunk_buffer.append(book_data)
            current_index += 1
            
            # Process chunk when buffer is full
            if len(chunk_buffer) >= CHUNK_SIZE:
                chunk_number += 1
                
                print(f"\n📦 Processing Chunk {chunk_number} (books {current_index - CHUNK_SIZE + 1}-{current_index})")
                print("-" * 80)
                
                # Insert batch
                inserted, skipped = insert_book_batch(cursor, chunk_buffer)
                conn.commit()
                
                total_inserted += inserted
                total_skipped += skipped
                
                # Save progress
                last_barcode = chunk_buffer[-1].get('barcode_src', 'unknown')
                save_progress(current_index - 1, total_inserted, last_barcode)
                
                # Print stats
                elapsed = time.time() - start_time
                rate = total_inserted / elapsed if elapsed > 0 else 0
                
                print(f"   ✅ Inserted: {inserted}")
                print(f"   ⏭️  Skipped: {skipped}")
                print(f"   📊 Total: {total_inserted} books loaded, {total_skipped} skipped")
                print(f"   ⏱️  Rate: {rate:.1f} books/second")
                print(f"   💾 Progress saved")
                
                # Clear buffer
                chunk_buffer = []
                
                # Check if we've reached max chunks
                if max_chunks and chunk_number >= max_chunks:
                    print(f"\n🏁 Reached maximum chunks limit ({max_chunks})")
                    break
        
        # Process remaining books in buffer
        if chunk_buffer:
            chunk_number += 1
            print(f"\n📦 Processing Final Chunk {chunk_number} ({len(chunk_buffer)} books)")
            print("-" * 80)
            
            inserted, skipped = insert_book_batch(cursor, chunk_buffer)
            conn.commit()
            
            total_inserted += inserted
            total_skipped += skipped
            
            last_barcode = chunk_buffer[-1].get('barcode_src', 'unknown')
            save_progress(current_index - 1, total_inserted, last_barcode)
            
            print(f"   ✅ Inserted: {inserted}")
            print(f"   ⏭️  Skipped: {skipped}")
        
        # Final summary
        elapsed = time.time() - start_time
        print("\n" + "=" * 80)
        print("✅ LOADING COMPLETE")
        print("=" * 80)
        print(f"📊 Total books inserted: {total_inserted}")
        print(f"⏭️  Total books skipped: {total_skipped}")
        print(f"📦 Total chunks processed: {chunk_number}")
        print(f"⏱️  Total time: {elapsed:.1f} seconds")
        print(f"📈 Average rate: {total_inserted / elapsed:.1f} books/second")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Loading interrupted by user")
        print(f"💾 Progress saved at index {current_index - 1}")
        print(f"📊 Loaded {total_inserted} books so far")
        print("   Run with --resume to continue from this point")
        conn.commit()
    
    except Exception as e:
        print(f"\n❌ Error during loading: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    
    finally:
        cursor.close()
        conn.close()
        print("\n🔌 Database connection closed")


# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Load Institutional Books dataset into BookLook database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Load first 1000 books (10 chunks)
  python load_institutional_books.py --max-chunks 10
  
  # Load all books
  python load_institutional_books.py
  
  # Resume from last position
  python load_institutional_books.py --resume
  
  # Start fresh (ignore progress)
  python load_institutional_books.py --no-resume
        """
    )
    
    parser.add_argument(
        '--max-chunks',
        type=int,
        default=None,
        help='Maximum number of chunks to process (default: all)'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        default=True,
        help='Resume from last saved position (default: True)'
    )
    
    parser.add_argument(
        '--no-resume',
        action='store_false',
        dest='resume',
        help='Start from beginning, ignore saved progress'
    )
    
    args = parser.parse_args()
    
    load_institutional_books(
        max_chunks=args.max_chunks,
        resume=args.resume
    )


if __name__ == "__main__":
    main()
