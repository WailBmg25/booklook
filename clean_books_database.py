#!/usr/bin/env python3
"""Clean books database - removes all books, authors, and book pages."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import SessionLocal
from models.book_model import Book
from models.author_model import Author
from models.book_page_model import BookPage
from models.genre_model import Genre

def clean_database():
    """Remove all books, book pages, and authors from database."""
    db = SessionLocal()
    
    try:
        print("🧹 Starting database cleanup...")
        print("="*60)
        
        # Get counts before deletion
        book_count = db.query(Book).count()
        page_count = db.query(BookPage).count()
        author_count = db.query(Author).count()
        
        print(f"📊 Current database state:")
        print(f"   - Books: {book_count}")
        print(f"   - Book Pages: {page_count}")
        print(f"   - Authors: {author_count}")
        print()
        
        if book_count == 0 and page_count == 0 and author_count == 0:
            print("✅ Database is already clean!")
            return
        
        # Confirm deletion
        response = input("⚠️  Are you sure you want to delete ALL books, pages, and authors? (yes/no): ")
        if response.lower() != 'yes':
            print("❌ Cleanup cancelled")
            return
        
        print("\n🗑️  Deleting data...")
        
        # Delete book pages first (due to foreign key constraints)
        print("   Deleting book pages...")
        db.query(BookPage).delete()
        db.commit()
        print(f"   ✅ Deleted {page_count} book pages")
        
        # Delete books (this will also remove associations)
        print("   Deleting books...")
        db.query(Book).delete()
        db.commit()
        print(f"   ✅ Deleted {book_count} books")
        
        # Delete authors
        print("   Deleting authors...")
        db.query(Author).delete()
        db.commit()
        print(f"   ✅ Deleted {author_count} authors")
        
        print()
        print("="*60)
        print("✅ Database cleanup complete!")
        print()
        print("📊 Final database state:")
        print(f"   - Books: {db.query(Book).count()}")
        print(f"   - Book Pages: {db.query(BookPage).count()}")
        print(f"   - Authors: {db.query(Author).count()}")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    clean_database()
