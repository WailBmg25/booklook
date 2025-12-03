#!/usr/bin/env python3
"""
Clear all books and related data from the database.
This will delete:
- All books
- All authors (that have no books)
- All genres (that have no books)
- All reviews
- All reading progress
- All favorites
- All book-author associations
- All book-genre associations
"""

import psycopg2
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env.production')

# Database configuration
DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'book_library'),
    'user': os.getenv('POSTGRES_USER', 'bookuser'),
    'password': os.getenv('POSTGRES_PASSWORD', 'bookpass123')
}

def clear_database():
    """Clear all book-related data from the database."""
    try:
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        print("\n⚠️  WARNING: This will delete ALL books and related data!")
        print("   - All books")
        print("   - All reviews")
        print("   - All reading progress")
        print("   - All favorites")
        print("   - All book-author associations")
        print("   - All book-genre associations")
        print("   - Orphaned authors and genres")
        
        response = input("\n❓ Are you sure you want to continue? (yes/no): ")
        
        if response.lower() != 'yes':
            print("❌ Operation cancelled.")
            return
        
        print("\n🗑️  Deleting data...")
        
        # Delete in correct order to respect foreign key constraints
        
        # 1. Delete reading progress
        cur.execute("DELETE FROM reading_progress")
        deleted = cur.rowcount
        print(f"   ✓ Deleted {deleted} reading progress records")
        
        # 2. Delete favorites
        cur.execute("DELETE FROM favorites")
        deleted = cur.rowcount
        print(f"   ✓ Deleted {deleted} favorites")
        
        # 3. Delete reviews
        cur.execute("DELETE FROM reviews")
        deleted = cur.rowcount
        print(f"   ✓ Deleted {deleted} reviews")
        
        # 4. Delete book-author associations
        cur.execute("DELETE FROM book_authors")
        deleted = cur.rowcount
        print(f"   ✓ Deleted {deleted} book-author associations")
        
        # 5. Delete book-genre associations
        cur.execute("DELETE FROM book_genres")
        deleted = cur.rowcount
        print(f"   ✓ Deleted {deleted} book-genre associations")
        
        # 6. Delete book pages (if exists)
        try:
            cur.execute("DELETE FROM book_pages")
            deleted = cur.rowcount
            print(f"   ✓ Deleted {deleted} book pages")
        except:
            pass
        
        # 7. Delete books
        cur.execute("DELETE FROM books")
        deleted = cur.rowcount
        print(f"   ✓ Deleted {deleted} books")
        
        # 8. Delete orphaned authors (optional)
        cur.execute("""
            DELETE FROM authors 
            WHERE id NOT IN (SELECT DISTINCT author_id FROM book_authors)
        """)
        deleted = cur.rowcount
        print(f"   ✓ Deleted {deleted} orphaned authors")
        
        # 9. Delete orphaned genres (optional)
        cur.execute("""
            DELETE FROM genres 
            WHERE id NOT IN (SELECT DISTINCT genre_id FROM book_genres)
        """)
        deleted = cur.rowcount
        print(f"   ✓ Deleted {deleted} orphaned genres")
        
        # Commit the transaction
        conn.commit()
        
        print("\n✅ All book data has been successfully deleted!")
        
        # Show remaining counts
        print("\n📊 Database status:")
        cur.execute("SELECT COUNT(*) FROM books")
        print(f"   Books: {cur.fetchone()[0]}")
        
        cur.execute("SELECT COUNT(*) FROM authors")
        print(f"   Authors: {cur.fetchone()[0]}")
        
        cur.execute("SELECT COUNT(*) FROM genres")
        print(f"   Genres: {cur.fetchone()[0]}")
        
        cur.execute("SELECT COUNT(*) FROM reviews")
        print(f"   Reviews: {cur.fetchone()[0]}")
        
        cur.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"\n❌ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    clear_database()
