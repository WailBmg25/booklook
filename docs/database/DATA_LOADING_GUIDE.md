# BookLook Data Loading Guide

## Overview

This guide provides comprehensive instructions for loading data into the BookLook database, including sample data, bulk imports, and the Institutional Books 1.0 dataset.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Database Setup](#database-setup)
3. [Sample Data Loading](#sample-data-loading)
4. [Bulk Data Import](#bulk-data-import)
5. [Institutional Books Dataset](#institutional-books-dataset)
6. [Data Validation](#data-validation)
7. [Performance Optimization](#performance-optimization)

---

## 1. Prerequisites

### Required Software
- Python 3.13+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional but recommended)

### Python Dependencies
```bash
pip install pandas sqlalchemy psycopg2-binary python-dotenv
```

### Environment Setup
Create a `.env` file in the `src/` directory:
```bash
DATABASE_URL=postgresql://booklook_user:password@localhost:5432/booklook
REDIS_URL=redis://localhost:6379
```

---

## 2. Database Setup

### Step 1: Start Docker Services

```bash
cd docker
docker-compose up -d
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379
- pgAdmin on port 5050 (optional)

### Step 2: Verify Database Connection

```bash
# Using psql
psql -h localhost -U booklook_user -d booklook

# Or using Python
python -c "from database import engine; print(engine.connect())"
```

### Step 3: Run Migrations

```bash
cd src
alembic upgrade head
```

This creates all tables, indexes, triggers, and views.

### Step 4: Verify Schema

```sql
-- Connect to database
psql -h localhost -U booklook_user -d booklook

-- List all tables
\dt

-- Expected output:
-- users, books, authors, genres, reviews, reading_progress
-- book_author, book_genre, user_favorites
```

---

## 3. Sample Data Loading

### Using the Existing Script

The project includes a sample data script:

```bash
python add_sample_data.py
```

This loads:
- 10 sample users
- 50 sample books
- 20 sample authors
- 10 sample genres
- 100 sample reviews
- Sample reading progress records

### Custom Sample Data Script

Create `load_sample_data.py`:

```python
from sqlalchemy.orm import Session
from database import SessionLocal
from models.user_model import User
from models.book_model import Book
from models.author_model import Author
from models.genre_model import Genre
from models.review_model import Review
from helpers.auth_helper import hash_password
from datetime import datetime, date

def create_sample_users(db: Session):
    """Create sample users"""
    users = [
        User(
            email="john.doe@example.com",
            first_name="John",
            last_name="Doe",
            password_hash=hash_password("password123"),
            is_active=True
        ),
        User(
            email="jane.smith@example.com",
            first_name="Jane",
            last_name="Smith",
            password_hash=hash_password("password123"),
            is_active=True
        ),
        User(
            email="admin@booklook.com",
            first_name="Admin",
            last_name="User",
            password_hash=hash_password("admin123"),
            is_active=True,
            is_admin=True
        )
    ]
    
    for user in users:
        db.add(user)
    
    db.commit()
    print(f"Created {len(users)} sample users")

def create_sample_genres(db: Session):
    """Create sample genres"""
    genres = [
        Genre(nom="Fiction", description="Fictional stories and novels"),
        Genre(nom="Science Fiction", description="Futuristic and scientific fiction"),
        Genre(nom="Mystery", description="Mystery and detective stories"),
        Genre(nom="Romance", description="Romantic novels"),
        Genre(nom="Thriller", description="Suspenseful thrillers"),
        Genre(nom="Fantasy", description="Fantasy and magical stories"),
        Genre(nom="Biography", description="Life stories of real people"),
        Genre(nom="History", description="Historical books"),
        Genre(nom="Science", description="Scientific books"),
        Genre(nom="Technology", description="Technology and programming books")
    ]
    
    for genre in genres:
        db.add(genre)
    
    db.commit()
    print(f"Created {len(genres)} sample genres")
    return genres

def create_sample_authors(db: Session):
    """Create sample authors"""
    authors = [
        Author(
            nom="Doe",
            prenom="John",
            biographie="A prolific writer of fiction",
            date_naissance=date(1970, 5, 15),
            nationalite="American"
        ),
        Author(
            nom="Smith",
            prenom="Jane",
            biographie="Award-winning science fiction author",
            date_naissance=date(1975, 8, 22),
            nationalite="British"
        ),
        Author(
            nom="Johnson",
            prenom="Robert",
            biographie="Mystery novelist",
            date_naissance=date(1965, 3, 10),
            nationalite="Canadian"
        )
    ]
    
    for author in authors:
        db.add(author)
    
    db.commit()
    print(f"Created {len(authors)} sample authors")
    return authors

def create_sample_books(db: Session, authors, genres):
    """Create sample books"""
    books = [
        Book(
            titre="The Great Adventure",
            isbn="978-0-123456-78-9",
            date_publication=date(2020, 1, 15),
            description="An epic adventure story",
            nombre_pages=350,
            total_pages=350,
            langue="English",
            editeur="Adventure Press",
            author_names=["John Doe"],
            genre_names=["Fiction", "Adventure"],
            word_count=95000
        ),
        Book(
            titre="Future World",
            isbn="978-0-234567-89-0",
            date_publication=date(2021, 6, 20),
            description="A science fiction masterpiece",
            nombre_pages=420,
            total_pages=420,
            langue="English",
            editeur="SciFi Publishing",
            author_names=["Jane Smith"],
            genre_names=["Science Fiction"],
            word_count=115000
        ),
        Book(
            titre="Mystery at Midnight",
            isbn="978-0-345678-90-1",
            date_publication=date(2019, 10, 5),
            description="A thrilling mystery",
            nombre_pages=280,
            total_pages=280,
            langue="English",
            editeur="Mystery House",
            author_names=["Robert Johnson"],
            genre_names=["Mystery", "Thriller"],
            word_count=78000
        )
    ]
    
    # Add relationships
    for book in books:
        db.add(book)
        # Add author relationships
        for author_name in book.author_names:
            author = db.query(Author).filter(
                (Author.nom + ' ' + Author.prenom).like(f"%{author_name}%")
            ).first()
            if author:
                book.auteurs.append(author)
        
        # Add genre relationships
        for genre_name in book.genre_names:
            genre = db.query(Genre).filter(Genre.nom == genre_name).first()
            if genre:
                book.genres.append(genre)
    
    db.commit()
    print(f"Created {len(books)} sample books")
    return books

def create_sample_reviews(db: Session, users, books):
    """Create sample reviews"""
    reviews = [
        Review(
            user_id=users[0].id,
            book_id=books[0].id,
            rating=5,
            title="Amazing book!",
            content="This book was absolutely fantastic. Couldn't put it down!"
        ),
        Review(
            user_id=users[1].id,
            book_id=books[0].id,
            rating=4,
            title="Great read",
            content="Really enjoyed this book. Highly recommended."
        ),
        Review(
            user_id=users[0].id,
            book_id=books[1].id,
            rating=5,
            title="Mind-blowing",
            content="The best science fiction I've read in years."
        )
    ]
    
    for review in reviews:
        db.add(review)
    
    db.commit()
    print(f"Created {len(reviews)} sample reviews")

if __name__ == "__main__":
    db = SessionLocal()
    
    try:
        print("Loading sample data...")
        
        create_sample_users(db)
        genres = create_sample_genres(db)
        authors = create_sample_authors(db)
        
        # Refresh to get IDs
        db.refresh(genres[0])
        db.refresh(authors[0])
        
        users = db.query(User).all()
        books = create_sample_books(db, authors, genres)
        
        # Refresh to get IDs
        db.refresh(books[0])
        
        create_sample_reviews(db, users, books)
        
        print("\nSample data loaded successfully!")
        print(f"Users: {len(users)}")
        print(f"Books: {len(books)}")
        print(f"Authors: {len(authors)}")
        print(f"Genres: {len(genres)}")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()
```

Run the script:
```bash
python load_sample_data.py
```

---

## 4. Bulk Data Import

### CSV Format Requirements

#### books.csv
```csv
id,title,isbn,publication_date,description,image_url,pages,language,publisher,author_names,genre_names,content_path,word_count
1,"Python Programming","978-0-123456-78-9","2023-01-15","A comprehensive guide to Python","https://example.com/img1.jpg","450","English","Tech Press","['John Doe', 'Jane Smith']","['Programming', 'Technology']","/content/book_1",125000
2,"Data Science Handbook","978-0-234567-89-0","2023-03-20","Complete data science guide","https://example.com/img2.jpg","520","English","Data Press","['Alice Johnson']","['Science', 'Technology']","/content/book_2",145000
```

#### authors.csv
```csv
id,last_name,first_name,biography,photo_url,birth_date,nationality
1,"Doe","John","John Doe is a software engineer and author","https://example.com/author1.jpg","1980-05-15","American"
2,"Smith","Jane","Jane Smith is a data scientist","https://example.com/author2.jpg","1985-08-22","British"
```

#### genres.csv
```csv
id,name,description
1,"Programming","Books about software development and programming languages"
2,"Technology","Books about technology and innovation"
3,"Science","Scientific books and research"
```

### Bulk Loading Script

Create `bulk_load_data.py`:

```python
import pandas as pd
import json
from sqlalchemy.orm import Session
from database import SessionLocal
from models.book_model import Book
from models.author_model import Author
from models.genre_model import Genre
from datetime import datetime

def load_genres_from_csv(csv_path: str, db: Session):
    """Load genres from CSV file"""
    print(f"Loading genres from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    genres = []
    for _, row in df.iterrows():
        genre = Genre(
            nom=row['name'],
            description=row.get('description', '')
        )
        genres.append(genre)
    
    db.bulk_save_objects(genres)
    db.commit()
    print(f"✓ Loaded {len(genres)} genres")

def load_authors_from_csv(csv_path: str, db: Session):
    """Load authors from CSV file"""
    print(f"Loading authors from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    authors = []
    for _, row in df.iterrows():
        author = Author(
            nom=row['last_name'],
            prenom=row.get('first_name', ''),
            biographie=row.get('biography', ''),
            photo_url=row.get('photo_url', ''),
            date_naissance=pd.to_datetime(row['birth_date']) if pd.notna(row.get('birth_date')) else None,
            nationalite=row.get('nationality', '')
        )
        authors.append(author)
    
    db.bulk_save_objects(authors)
    db.commit()
    print(f"✓ Loaded {len(authors)} authors")

def load_books_from_csv(csv_path: str, db: Session, batch_size: int = 1000):
    """Load books from CSV file in batches"""
    print(f"Loading books from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    total_loaded = 0
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        books = []
        
        for _, row in batch.iterrows():
            # Parse JSON arrays
            author_names = json.loads(row['author_names']) if isinstance(row['author_names'], str) else []
            genre_names = json.loads(row['genre_names']) if isinstance(row['genre_names'], str) else []
            
            book = Book(
                titre=row['title'],
                isbn=row['isbn'],
                date_publication=pd.to_datetime(row['publication_date']) if pd.notna(row.get('publication_date')) else None,
                description=row.get('description', ''),
                image_url=row.get('image_url', ''),
                nombre_pages=int(row['pages']) if pd.notna(row.get('pages')) else None,
                total_pages=int(row['pages']) if pd.notna(row.get('pages')) else None,
                langue=row.get('language', 'English'),
                editeur=row.get('publisher', ''),
                author_names=author_names,
                genre_names=genre_names,
                content_path=row.get('content_path', ''),
                word_count=int(row['word_count']) if pd.notna(row.get('word_count')) else None
            )
            books.append(book)
        
        db.bulk_save_objects(books)
        db.commit()
        total_loaded += len(books)
        print(f"  Loaded batch {i//batch_size + 1}: {len(books)} books (Total: {total_loaded})")
    
    print(f"✓ Loaded {total_loaded} books total")

def load_all_data(data_dir: str):
    """Load all data from CSV files"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("Starting bulk data import...")
        print("=" * 60)
        
        # Load in order (genres and authors first, then books)
        load_genres_from_csv(f"{data_dir}/genres.csv", db)
        load_authors_from_csv(f"{data_dir}/authors.csv", db)
        load_books_from_csv(f"{data_dir}/books.csv", db)
        
        print("=" * 60)
        print("Bulk data import completed successfully!")
        print("=" * 60)
        
        # Print statistics
        from models.book_model import Book
        from models.author_model import Author
        from models.genre_model import Genre
        
        book_count = db.query(Book).count()
        author_count = db.query(Author).count()
        genre_count = db.query(Genre).count()
        
        print(f"\nDatabase Statistics:")
        print(f"  Books: {book_count}")
        print(f"  Authors: {author_count}")
        print(f"  Genres: {genre_count}")
        
    except Exception as e:
        print(f"\n✗ Error during import: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python bulk_load_data.py <data_directory>")
        print("Example: python bulk_load_data.py /data/institutional_books")
        sys.exit(1)
    
    data_directory = sys.argv[1]
    load_all_data(data_directory)
```

Run the script:
```bash
python bulk_load_data.py /path/to/data/directory
```

---

## 5. Institutional Books Dataset

### Expected Dataset Structure

```
/data/institutional_books/
├── books.csv
├── authors.csv
├── genres.csv
└── content/
    ├── book_1/
    │   ├── metadata.json
    │   ├── page_001.txt
    │   ├── page_002.txt
    │   └── ...
    ├── book_2/
    │   └── ...
    └── ...
```

### Content File Format

Each book's content should be split into pages:

**metadata.json**:
```json
{
  "book_id": 1,
  "title": "Python Programming",
  "total_pages": 450,
  "words_per_page": 250,
  "total_words": 112500
}
```

**page_001.txt**:
```
Chapter 1: Introduction to Python

Python is a high-level, interpreted programming language...
[Content continues for ~250-300 words per page]
```

### Loading Institutional Dataset

Create `load_institutional_dataset.py`:

```python
import os
import json
from pathlib import Path
from bulk_load_data import load_all_data

def validate_dataset_structure(data_dir: str) -> bool:
    """Validate that the dataset has the required structure"""
    required_files = ['books.csv', 'authors.csv', 'genres.csv']
    
    for file in required_files:
        file_path = os.path.join(data_dir, file)
        if not os.path.exists(file_path):
            print(f"✗ Missing required file: {file}")
            return False
        print(f"✓ Found {file}")
    
    content_dir = os.path.join(data_dir, 'content')
    if not os.path.exists(content_dir):
        print(f"✗ Missing content directory")
        return False
    print(f"✓ Found content directory")
    
    return True

def count_dataset_records(data_dir: str):
    """Count records in the dataset"""
    import pandas as pd
    
    books_df = pd.read_csv(os.path.join(data_dir, 'books.csv'))
    authors_df = pd.read_csv(os.path.join(data_dir, 'authors.csv'))
    genres_df = pd.read_csv(os.path.join(data_dir, 'genres.csv'))
    
    print(f"\nDataset Statistics:")
    print(f"  Books: {len(books_df):,}")
    print(f"  Authors: {len(authors_df):,}")
    print(f"  Genres: {len(genres_df):,}")
    
    # Estimate size
    content_dir = os.path.join(data_dir, 'content')
    if os.path.exists(content_dir):
        total_size = sum(
            os.path.getsize(os.path.join(dirpath, filename))
            for dirpath, dirnames, filenames in os.walk(content_dir)
            for filename in filenames
        )
        print(f"  Content Size: {total_size / (1024**3):.2f} GB")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python load_institutional_dataset.py <dataset_directory>")
        sys.exit(1)
    
    dataset_dir = sys.argv[1]
    
    print("=" * 60)
    print("Institutional Books Dataset Loader")
    print("=" * 60)
    
    # Validate structure
    if not validate_dataset_structure(dataset_dir):
        print("\n✗ Dataset validation failed")
        sys.exit(1)
    
    print("\n✓ Dataset validation passed")
    
    # Count records
    count_dataset_records(dataset_dir)
    
    # Confirm before loading
    response = input("\nProceed with data loading? (yes/no): ")
    if response.lower() != 'yes':
        print("Loading cancelled")
        sys.exit(0)
    
    # Load data
    load_all_data(dataset_dir)
```

Run the script:
```bash
python load_institutional_dataset.py /data/institutional_books
```

---

## 6. Data Validation

### Validation Script

Create `validate_data.py`:

```python
from sqlalchemy.orm import Session
from database import SessionLocal
from models.book_model import Book
from models.author_model import Author
from models.genre_model import Genre
from models.user_model import User
from models.review_model import Review

def validate_database():
    """Validate database integrity"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("Database Validation")
        print("=" * 60)
        
        # Count records
        book_count = db.query(Book).count()
        author_count = db.query(Author).count()
        genre_count = db.query(Genre).count()
        user_count = db.query(User).count()
        review_count = db.query(Review).count()
        
        print(f"\nRecord Counts:")
        print(f"  Books: {book_count:,}")
        print(f"  Authors: {author_count:,}")
        print(f"  Genres: {genre_count:,}")
        print(f"  Users: {user_count:,}")
        print(f"  Reviews: {review_count:,}")
        
        # Check for data integrity issues
        print(f"\nData Integrity Checks:")
        
        # Books without authors
        books_no_authors = db.query(Book).filter(
            (Book.author_names == None) | (Book.author_names == [])
        ).count()
        print(f"  Books without authors: {books_no_authors}")
        
        # Books without genres
        books_no_genres = db.query(Book).filter(
            (Book.genre_names == None) | (Book.genre_names == [])
        ).count()
        print(f"  Books without genres: {books_no_genres}")
        
        # Books without ISBN
        books_no_isbn = db.query(Book).filter(Book.isbn == None).count()
        print(f"  Books without ISBN: {books_no_isbn}")
        
        # Check rating consistency
        books_with_reviews = db.query(Book).filter(Book.review_count > 0).all()
        rating_mismatches = 0
        for book in books_with_reviews:
            actual_count = db.query(Review).filter(Review.book_id == book.id).count()
            if actual_count != book.review_count:
                rating_mismatches += 1
        
        print(f"  Books with rating mismatches: {rating_mismatches}")
        
        # Sample data
        print(f"\nSample Books:")
        sample_books = db.query(Book).limit(5).all()
        for book in sample_books:
            print(f"  - {book.titre} (ISBN: {book.isbn})")
        
        print("\n" + "=" * 60)
        print("Validation Complete")
        print("=" * 60)
        
    finally:
        db.close()

if __name__ == "__main__":
    validate_database()
```

Run validation:
```bash
python validate_data.py
```

---

## 7. Performance Optimization

### Analyze Tables

After loading data, analyze tables for query optimization:

```sql
-- Analyze all tables
ANALYZE users;
ANALYZE books;
ANALYZE authors;
ANALYZE genres;
ANALYZE reviews;
ANALYZE reading_progress;

-- Vacuum and analyze
VACUUM ANALYZE books;
VACUUM ANALYZE reviews;
```

### Check Index Usage

```sql
-- Check index usage statistics
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as index_scans,
    idx_tup_read as tuples_read,
    idx_tup_fetch as tuples_fetched
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

### Optimize Queries

```python
# Example: Batch update denormalized fields
from database import SessionLocal
from models.book_model import Book

db = SessionLocal()

books = db.query(Book).all()
for book in books:
    book.update_denormalized_fields()

db.commit()
db.close()
```

---

## Troubleshooting

### Common Issues

1. **Out of Memory**
   - Reduce batch size in bulk loading
   - Increase PostgreSQL shared_buffers

2. **Slow Imports**
   - Disable indexes during import, rebuild after
   - Use COPY instead of INSERT for large datasets

3. **Duplicate Keys**
   - Check for duplicate ISBNs in source data
   - Use ON CONFLICT DO NOTHING for idempotent imports

### Performance Tips

- Load data in order: genres → authors → books → reviews
- Use batch inserts (1000-5000 records per batch)
- Disable triggers during bulk import if needed
- Run VACUUM ANALYZE after large imports
- Monitor disk space (dataset can be 100-300GB)

---

## Summary

This guide covers:
- ✓ Database setup and migrations
- ✓ Sample data loading for development
- ✓ Bulk CSV import for large datasets
- ✓ Institutional Books dataset integration
- ✓ Data validation and integrity checks
- ✓ Performance optimization techniques

For questions or issues, refer to the main project documentation or contact the development team.
