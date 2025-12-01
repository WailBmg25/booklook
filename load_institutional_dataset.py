#!/usr/bin/env python
"""
Script to load institutional book dataset into BookLook database.

Dataset Format:
- Multiple CSV files with book data
- Fields: isbn, lccn, title, author, text (array of pages), publication_date, cover_url
- Text field contains array of page content

Usage:
    python load_institutional_dataset.py /path/to/csv/files
    python load_institutional_dataset.py /path/to/csv/files --batch-size 100
    python load_institutional_dataset.py /path/to/csv/files --skip-existing
"""

import sys
import os
import csv
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging
import requests
import time
import hashlib

# Increase CSV field size limit to handle large book content
csv.field_size_limit(10 * 1024 * 1024)  # 10MB per field

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import SessionLocal
from models.book_model import Book
from models.book_page_model import BookPage
from models.author_model import Author
from models.genre_model import Genre
from sqlalchemy.exc import IntegrityError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dataset_import.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DatasetLoader:
    """Loader for institutional book dataset."""
    
    def __init__(self, db_session, batch_size: int = 100, skip_existing: bool = False, 
                 fetch_isbn: bool = True):
        self.db = db_session
        self.batch_size = batch_size
        self.skip_existing = skip_existing
        self.fetch_isbn = fetch_isbn
        
        # Statistics
        self.stats = {
            'total_processed': 0,
            'books_created': 0,
            'books_skipped': 0,
            'pages_created': 0,
            'authors_created': 0,
            'isbn_fetched': 0,
            'isbn_generated': 0,
            'errors': 0,
            'error_details': []
        }
        
        # Rate limiting for API calls
        self.last_api_call = 0
        self.api_delay = 1.0  # seconds between API calls
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse publication date from various formats."""
        if not date_str or date_str.strip() == '':
            return None
        
        # Try different date formats
        formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y',
            '%m/%d/%Y',
            '%d/%m/%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str).strip(), fmt).date()
            except:
                continue
        
        # Try to extract just the year
        try:
            year = int(str(date_str)[:4])
            if 1000 <= year <= 9999:
                return datetime(year, 1, 1).date()
        except:
            pass
        
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def parse_text_pages(self, text_data: Any) -> List[str]:
        """Parse text pages from various formats."""
        if not text_data:
            return []
        
        # If it's already a list
        if isinstance(text_data, list):
            return [str(page) for page in text_data if page]
        
        # If it's a JSON string
        if isinstance(text_data, str):
            try:
                parsed = json.loads(text_data)
                if isinstance(parsed, list):
                    return [str(page) for page in parsed if page]
                return [str(parsed)]
            except json.JSONDecodeError:
                # Treat as single page
                return [text_data]
        
        return [str(text_data)]
    
    def extract_author_name(self, author_str: str) -> tuple:
        """Extract first and last name from author string."""
        if not author_str or author_str.strip() == '':
            return "Unknown", "Author"
        
        author_str = author_str.strip()
        
        # Handle "Last, First" format
        if ',' in author_str:
            parts = author_str.split(',', 1)
            last_name = parts[0].strip()
            first_name = parts[1].strip() if len(parts) > 1 else ""
            return first_name, last_name
        
        # Handle "First Last" format
        parts = author_str.split()
        if len(parts) >= 2:
            first_name = ' '.join(parts[:-1])
            last_name = parts[-1]
            return first_name, last_name
        
        # Single name
        return "", author_str
    
    def get_or_create_author(self, author_str: str) -> Optional[Author]:
        """Get existing author or create new one."""
        if not author_str or author_str.strip() == '':
            return None
        
        first_name, last_name = self.extract_author_name(author_str)
        
        # Check if author exists
        author = self.db.query(Author).filter(
            Author.nom == last_name,
            Author.prenom == first_name
        ).first()
        
        if not author:
            author = Author(
                nom=last_name,
                prenom=first_name
            )
            self.db.add(author)
            self.db.flush()  # Get the ID without committing
            self.stats['authors_created'] += 1
            logger.debug(f"Created author: {first_name} {last_name}")
        
        return author
    
    def fetch_isbn_from_openlibrary(self, title: str, author: str) -> Optional[str]:
        """Fetch ISBN from Open Library API based on title and author."""
        if not self.fetch_isbn:
            return None
        
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last_call = current_time - self.last_api_call
            if time_since_last_call < self.api_delay:
                time.sleep(self.api_delay - time_since_last_call)
            
            # Build search query
            query_parts = []
            if title:
                query_parts.append(f'title:"{title}"')
            if author:
                query_parts.append(f'author:"{author}"')
            
            if not query_parts:
                return None
            
            query = ' '.join(query_parts)
            url = f"https://openlibrary.org/search.json?q={query}&limit=1"
            
            self.last_api_call = time.time()
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                docs = data.get('docs', [])
                
                if docs:
                    # Try to get ISBN-13 first, then ISBN-10
                    isbn_list = docs[0].get('isbn', [])
                    if isbn_list:
                        # Prefer ISBN-13 (13 digits)
                        for isbn in isbn_list:
                            if len(isbn) == 13:
                                logger.info(f"✓ Fetched ISBN from Open Library: {isbn}")
                                self.stats['isbn_fetched'] += 1
                                return isbn
                        # Fall back to first ISBN
                        logger.info(f"✓ Fetched ISBN from Open Library: {isbn_list[0]}")
                        self.stats['isbn_fetched'] += 1
                        return isbn_list[0]
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to fetch ISBN from Open Library: {str(e)}")
            return None
    
    def generate_isbn_substitute(self, title: str, author: str) -> str:
        """Generate a unique identifier to use as ISBN substitute."""
        # Create a hash-based identifier
        content = f"{title}|{author}".lower().strip()
        hash_obj = hashlib.md5(content.encode())
        hash_hex = hash_obj.hexdigest()
        
        # Format as ISBN-like: GEN- prefix + 10 chars from hash
        isbn_substitute = f"GEN-{hash_hex[:10].upper()}"
        
        self.stats['isbn_generated'] += 1
        logger.info(f"Generated ISBN substitute: {isbn_substitute}")
        
        return isbn_substitute
    
    def create_book_with_pages(self, row: Dict[str, Any]) -> bool:
        """Create book and its pages from CSV row."""
        try:
            isbn = row.get('isbn', '').strip()
            title = row.get('title', 'Untitled').strip()
            author_str = row.get('author', '').strip()
            
            # Handle missing ISBN
            if not isbn:
                logger.warning(f"Book without ISBN: {title} by {author_str}")
                
                # Try to fetch ISBN from Open Library
                if self.fetch_isbn:
                    fetched_isbn = self.fetch_isbn_from_openlibrary(title, author_str)
                    if fetched_isbn:
                        isbn = fetched_isbn
                        logger.info(f"Using fetched ISBN: {isbn}")
                
                # If still no ISBN, generate a substitute
                if not isbn:
                    isbn = self.generate_isbn_substitute(title, author_str)
                    logger.info(f"Using generated ISBN: {isbn}")
            
            # Check if book already exists
            if self.skip_existing:
                existing = self.db.query(Book).filter(Book.isbn == isbn).first()
                if existing:
                    logger.info(f"Skipping existing book: {isbn}")
                    self.stats['books_skipped'] += 1
                    return False
            
            # Parse data
            publication_date = self.parse_date(row.get('publication_date', ''))
            cover_url = row.get('cover_url', '').strip()
            lccn = row.get('lccn', '').strip()
            text_pages = self.parse_text_pages(row.get('text', []))
            
            # Get or create author
            author = self.get_or_create_author(author_str)
            author_names = [f"{author.prenom} {author.nom}".strip()] if author else []
            
            # Calculate statistics
            total_words = sum(len(page.split()) for page in text_pages)
            total_pages = len(text_pages)
            
            # Create book
            book = Book(
                titre=title,
                isbn=isbn,
                date_publication=publication_date,
                image_url=cover_url if cover_url else None,
                author_names=author_names if author_names else None,
                total_pages=total_pages,
                nombre_pages=total_pages,
                word_count=total_words,
                langue="English",  # Default, adjust if you have language data
                description=f"LCCN: {lccn}" if lccn else None
            )
            
            self.db.add(book)
            self.db.flush()  # Get book ID
            
            # Link author
            if author:
                book.auteurs.append(author)
            
            # Create pages
            pages_created = 0
            for page_num, page_content in enumerate(text_pages, start=1):
                if not page_content or not page_content.strip():
                    continue
                
                page = BookPage(
                    book_id=book.id,
                    page_number=page_num,
                    content=page_content.strip()
                )
                page.calculate_word_count()
                self.db.add(page)
                pages_created += 1
            
            self.db.commit()
            
            self.stats['books_created'] += 1
            self.stats['pages_created'] += pages_created
            
            logger.info(f"✓ Created book: {title} (ISBN: {isbn}) with {pages_created} pages")
            return True
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error for ISBN {row.get('isbn', 'unknown')}: {str(e)}")
            self.stats['errors'] += 1
            self.stats['error_details'].append({
                'isbn': row.get('isbn', 'unknown'),
                'title': row.get('title', 'unknown'),
                'error': 'Duplicate ISBN or constraint violation'
            })
            return False
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error processing book {row.get('isbn', 'unknown')}: {str(e)}")
            self.stats['errors'] += 1
            self.stats['error_details'].append({
                'isbn': row.get('isbn', 'unknown'),
                'title': row.get('title', 'unknown'),
                'error': str(e)
            })
            return False
    
    def load_csv_file(self, csv_path: Path) -> None:
        """Load books from a single CSV file."""
        logger.info(f"Processing file: {csv_path}")
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                batch = []
                for row in reader:
                    batch.append(row)
                    self.stats['total_processed'] += 1
                    
                    # Process in batches
                    if len(batch) >= self.batch_size:
                        self.process_batch(batch)
                        batch = []
                
                # Process remaining
                if batch:
                    self.process_batch(batch)
                    
        except Exception as e:
            logger.error(f"Error reading CSV file {csv_path}: {str(e)}")
    
    def process_batch(self, batch: List[Dict[str, Any]]) -> None:
        """Process a batch of books."""
        logger.info(f"Processing batch of {len(batch)} books...")
        
        for row in batch:
            self.create_book_with_pages(row)
        
        # Log progress
        logger.info(f"Progress: {self.stats['books_created']} books created, "
                   f"{self.stats['pages_created']} pages created, "
                   f"{self.stats['errors']} errors")
    
    def load_directory(self, directory: Path) -> None:
        """Load all CSV files from a directory."""
        csv_files = list(directory.glob('*.csv'))
        
        if not csv_files:
            logger.error(f"No CSV files found in {directory}")
            return
        
        logger.info(f"Found {len(csv_files)} CSV files to process")
        
        for csv_file in sorted(csv_files):
            self.load_csv_file(csv_file)
    
    def print_summary(self) -> None:
        """Print import summary."""
        print("\n" + "="*60)
        print("IMPORT SUMMARY")
        print("="*60)
        print(f"Total rows processed: {self.stats['total_processed']:,}")
        print(f"Books created: {self.stats['books_created']:,}")
        print(f"Books skipped: {self.stats['books_skipped']:,}")
        print(f"Pages created: {self.stats['pages_created']:,}")
        print(f"Authors created: {self.stats['authors_created']:,}")
        print(f"ISBNs fetched from API: {self.stats['isbn_fetched']:,}")
        print(f"ISBNs generated: {self.stats['isbn_generated']:,}")
        print(f"Errors: {self.stats['errors']:,}")
        
        if self.stats['error_details']:
            print(f"\nFirst 10 errors:")
            for error in self.stats['error_details'][:10]:
                print(f"  - {error['isbn']}: {error['error']}")
        
        print("="*60)
        
        # Save detailed error log
        if self.stats['error_details']:
            error_file = 'import_errors.json'
            with open(error_file, 'w') as f:
                json.dump(self.stats['error_details'], f, indent=2)
            print(f"\nDetailed errors saved to: {error_file}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Load institutional book dataset into BookLook database'
    )
    parser.add_argument(
        'data_path',
        help='Path to CSV file or directory containing CSV files'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Number of books to process in each batch (default: 100)'
    )
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip books that already exist in database'
    )
    parser.add_argument(
        '--no-fetch-isbn',
        action='store_true',
        help='Do not attempt to fetch missing ISBNs from Open Library API'
    )
    
    args = parser.parse_args()
    
    # Validate path
    data_path = Path(args.data_path)
    if not data_path.exists():
        logger.error(f"Path does not exist: {data_path}")
        sys.exit(1)
    
    # Create database session
    db = SessionLocal()
    
    try:
        logger.info("="*60)
        logger.info("INSTITUTIONAL DATASET IMPORT")
        logger.info("="*60)
        logger.info(f"Data path: {data_path}")
        logger.info(f"Batch size: {args.batch_size}")
        logger.info(f"Skip existing: {args.skip_existing}")
        logger.info(f"Fetch missing ISBNs: {not args.no_fetch_isbn}")
        logger.info("="*60)
        
        # Create loader
        loader = DatasetLoader(
            db_session=db,
            batch_size=args.batch_size,
            skip_existing=args.skip_existing,
            fetch_isbn=not args.no_fetch_isbn
        )
        
        # Load data
        start_time = datetime.now()
        
        if data_path.is_file():
            loader.load_csv_file(data_path)
        else:
            loader.load_directory(data_path)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Print summary
        loader.print_summary()
        print(f"\nTotal time: {duration:.2f} seconds")
        print(f"Average: {loader.stats['books_created']/duration:.2f} books/second")
        
    except KeyboardInterrupt:
        logger.warning("\nImport interrupted by user")
        db.rollback()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
