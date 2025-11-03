#!/usr/bin/env python
"""Script to add sample data to the database for testing."""

import sys
from pathlib import Path
from datetime import date

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from database import SessionLocal
from models.book_model import Book
from models.author_model import Author
from models.genre_model import Genre
from models.associations import book_author_association, book_genre_association

def add_sample_data():
    """Add sample books, authors, and genres to the database."""
    db = SessionLocal()
    
    try:
        # Check if data already exists
        book_count = db.query(Book).count()
        if book_count > 0:
            print(f"Sample data already exists! ({book_count} books)")
            return
        
        # Create genres
        print("Creating genres...")
        fiction = Genre(nom="Fiction", description="Fictional works")
        scifi = Genre(nom="Science Fiction", description="Science fiction novels")
        fantasy = Genre(nom="Fantasy", description="Fantasy novels")
        programming = Genre(nom="Programming", description="Programming books")
        
        db.add_all([fiction, scifi, fantasy, programming])
        db.commit()
        
        # Create authors
        print("Creating authors...")
        author1 = Author(nom="Doe", prenom="John", biographie="Famous author")
        author2 = Author(nom="Smith", prenom="Jane", biographie="Bestselling writer")
        author3 = Author(nom="Johnson", prenom="Bob", biographie="Tech writer")
        
        db.add_all([author1, author2, author3])
        db.commit()
        
        # Create books
        print("Creating books...")
        book1 = Book(
            titre="The Great Adventure",
            isbn="978-1234567890",
            date_publication=date(2020, 1, 15),
            description="An amazing adventure story",
            nombre_pages=350,
            langue="English",
            editeur="Publisher One",
            author_names=["John Doe"],
            genre_names=["Fiction", "Fantasy"],
            word_count=85000,
            total_pages=350,
            average_rating=4.5,
            review_count=10,
            content_path="/books/great_adventure.txt"
        )
        
        book2 = Book(
            titre="Python Programming Guide",
            isbn="978-0987654321",
            date_publication=date(2021, 3, 20),
            description="Complete guide to Python programming",
            nombre_pages=500,
            langue="English",
            editeur="Tech Publishers",
            author_names=["Bob Johnson"],
            genre_names=["Programming"],
            word_count=120000,
            total_pages=500,
            average_rating=4.8,
            review_count=25,
            content_path="/books/python_guide.txt"
        )
        
        book3 = Book(
            titre="Space Odyssey",
            isbn="978-1122334455",
            date_publication=date(2019, 7, 10),
            description="A journey through space and time",
            nombre_pages=420,
            langue="English",
            editeur="SciFi Press",
            author_names=["Jane Smith"],
            genre_names=["Science Fiction"],
            word_count=95000,
            total_pages=420,
            average_rating=4.2,
            review_count=15,
            content_path="/books/space_odyssey.txt"
        )
        
        book4 = Book(
            titre="Mystery Manor",
            isbn="978-5566778899",
            date_publication=date(2022, 11, 5),
            description="A thrilling mystery novel",
            nombre_pages=280,
            langue="English",
            editeur="Mystery House",
            author_names=["John Doe", "Jane Smith"],
            genre_names=["Fiction"],
            word_count=70000,
            total_pages=280,
            average_rating=3.9,
            review_count=8,
            content_path="/books/mystery_manor.txt"
        )
        
        book5 = Book(
            titre="Fantasy Realm",
            isbn="978-9988776655",
            date_publication=date(2023, 5, 12),
            description="Epic fantasy adventure",
            nombre_pages=600,
            langue="English",
            editeur="Fantasy World",
            author_names=["Jane Smith"],
            genre_names=["Fantasy", "Fiction"],
            word_count=150000,
            total_pages=600,
            average_rating=4.7,
            review_count=30,
            content_path="/books/fantasy_realm.txt"
        )
        
        db.add_all([book1, book2, book3, book4, book5])
        db.commit()
        
        # Link books to authors
        print("Linking books to authors...")
        db.execute(book_author_association.insert().values(book_id=book1.id, author_id=author1.id))
        db.execute(book_author_association.insert().values(book_id=book2.id, author_id=author3.id))
        db.execute(book_author_association.insert().values(book_id=book3.id, author_id=author2.id))
        db.execute(book_author_association.insert().values(book_id=book4.id, author_id=author1.id))
        db.execute(book_author_association.insert().values(book_id=book4.id, author_id=author2.id))
        db.execute(book_author_association.insert().values(book_id=book5.id, author_id=author2.id))
        
        # Link books to genres
        print("Linking books to genres...")
        db.execute(book_genre_association.insert().values(book_id=book1.id, genre_id=fiction.id))
        db.execute(book_genre_association.insert().values(book_id=book1.id, genre_id=fantasy.id))
        db.execute(book_genre_association.insert().values(book_id=book2.id, genre_id=programming.id))
        db.execute(book_genre_association.insert().values(book_id=book3.id, genre_id=scifi.id))
        db.execute(book_genre_association.insert().values(book_id=book4.id, genre_id=fiction.id))
        db.execute(book_genre_association.insert().values(book_id=book5.id, genre_id=fantasy.id))
        db.execute(book_genre_association.insert().values(book_id=book5.id, genre_id=fiction.id))
        
        db.commit()
        
        print(f"\n✅ Successfully added sample data:")
        print(f"   - {db.query(Genre).count()} genres")
        print(f"   - {db.query(Author).count()} authors")
        print(f"   - {db.query(Book).count()} books")
        
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    add_sample_data()
