"""Admin CSV import/export routes."""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response
from sqlalchemy.orm import Session
from typing import List
import csv
import io
from datetime import datetime

from database import get_db
from models.user_model import User
from models.book_model import Book
from models.review_model import Review
from helpers.auth_helper import AuthHelper

router = APIRouter(prefix="/admin", tags=["Admin CSV"])


# ============================================
# USERS CSV ENDPOINTS
# ============================================

@router.get("/users/export")
def export_users_csv(db: Session = Depends(get_db)):
    """Export all users to CSV."""
    users = db.query(User).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Email', 'First Name', 'Last Name', 'Is Active', 
        'Is Admin', 'Created At', 'Reviews Count', 'Favorites Count'
    ])
    
    # Write data
    for user in users:
        writer.writerow([
            user.id,
            user.email,
            user.first_name,
            user.last_name,
            user.is_active,
            user.is_admin,
            user.created_at.isoformat() if user.created_at else '',
            user.get_reviews_count(),
            user.get_favorites_count()
        ])
    
    # Return CSV
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=users_export_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


@router.post("/users/import")
async def import_users_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Import users from CSV file.
    
    Expected CSV format:
    Email,First Name,Last Name,Password,Is Active,Is Admin
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = await file.read()
    decoded = content.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(decoded))
    
    imported_count = 0
    errors = []
    
    for row_num, row in enumerate(csv_reader, start=2):
        try:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == row['Email']).first()
            if existing_user:
                errors.append(f"Row {row_num}: User with email {row['Email']} already exists")
                continue
            
            # Create new user
            auth_helper = AuthHelper()
            user = User(
                email=row['Email'],
                first_name=row['First Name'],
                last_name=row['Last Name'],
                password_hash=auth_helper.hash_password(row.get('Password', 'password123')),
                is_active=row.get('Is Active', 'true').lower() == 'true',
                is_admin=row.get('Is Admin', 'false').lower() == 'true'
            )
            user.update_legacy_fields()
            
            db.add(user)
            imported_count += 1
            
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
    
    db.commit()
    
    return {
        "imported_count": imported_count,
        "errors": errors,
        "total_rows": row_num - 1 if 'row_num' in locals() else 0
    }


# ============================================
# BOOKS CSV ENDPOINTS
# ============================================

@router.get("/books/export")
def export_books_csv(db: Session = Depends(get_db)):
    """Export all books to CSV."""
    books = db.query(Book).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'Title', 'ISBN', 'Authors', 'Genres', 'Publication Date',
        'Pages', 'Language', 'Publisher', 'Average Rating', 'Review Count',
        'Word Count', 'Description'
    ])
    
    # Write data
    for book in books:
        writer.writerow([
            book.id,
            book.titre,
            book.isbn,
            '; '.join(book.author_names) if book.author_names else '',
            '; '.join(book.genre_names) if book.genre_names else '',
            book.date_publication.isoformat() if book.date_publication else '',
            book.nombre_pages or '',
            book.langue or '',
            book.editeur or '',
            float(book.average_rating) if book.average_rating else 0.0,
            book.review_count or 0,
            book.word_count or '',
            book.description or ''
        ])
    
    # Return CSV
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=books_export_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


@router.post("/books/import")
async def import_books_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Import books from CSV file.
    
    Expected CSV format:
    Title,ISBN,Authors,Genres,Publication Date,Pages,Language,Publisher,Description
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = await file.read()
    decoded = content.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(decoded))
    
    imported_count = 0
    errors = []
    
    for row_num, row in enumerate(csv_reader, start=2):
        try:
            # Check if book already exists
            if row.get('ISBN'):
                existing_book = db.query(Book).filter(Book.isbn == row['ISBN']).first()
                if existing_book:
                    errors.append(f"Row {row_num}: Book with ISBN {row['ISBN']} already exists")
                    continue
            
            # Parse authors and genres
            authors = [a.strip() for a in row.get('Authors', '').split(';') if a.strip()]
            genres = [g.strip() for g in row.get('Genres', '').split(';') if g.strip()]
            
            # Parse date
            pub_date = None
            if row.get('Publication Date'):
                try:
                    pub_date = datetime.fromisoformat(row['Publication Date']).date()
                except:
                    pass
            
            # Create new book
            book = Book(
                titre=row['Title'],
                isbn=row.get('ISBN', ''),
                author_names=authors if authors else None,
                genre_names=genres if genres else None,
                date_publication=pub_date,
                nombre_pages=int(row['Pages']) if row.get('Pages') and row['Pages'].isdigit() else None,
                langue=row.get('Language', 'English'),
                editeur=row.get('Publisher', ''),
                description=row.get('Description', '')
            )
            
            db.add(book)
            imported_count += 1
            
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
    
    db.commit()
    
    return {
        "imported_count": imported_count,
        "errors": errors,
        "total_rows": row_num - 1 if 'row_num' in locals() else 0
    }


# ============================================
# REVIEWS CSV ENDPOINTS
# ============================================

@router.get("/reviews/export")
def export_reviews_csv(db: Session = Depends(get_db)):
    """Export all reviews to CSV."""
    reviews = db.query(Review).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'ID', 'User ID', 'User Email', 'Book ID', 'Book Title', 
        'Rating', 'Title', 'Content', 'Is Flagged', 'Created At'
    ])
    
    # Write data
    for review in reviews:
        writer.writerow([
            review.id,
            review.user_id,
            review.user.email if review.user else '',
            review.book_id,
            review.book.titre if review.book else '',
            review.rating,
            review.title or '',
            review.content or '',
            review.is_flagged,
            review.created_at.isoformat() if review.created_at else ''
        ])
    
    # Return CSV
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=reviews_export_{datetime.now().strftime('%Y%m%d')}.csv"
        }
    )


@router.post("/reviews/import")
async def import_reviews_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Import reviews from CSV file.
    
    Expected CSV format:
    User Email,Book ISBN,Rating,Title,Content
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    content = await file.read()
    decoded = content.decode('utf-8')
    csv_reader = csv.DictReader(io.StringIO(decoded))
    
    imported_count = 0
    errors = []
    
    for row_num, row in enumerate(csv_reader, start=2):
        try:
            # Find user
            user = db.query(User).filter(User.email == row['User Email']).first()
            if not user:
                errors.append(f"Row {row_num}: User with email {row['User Email']} not found")
                continue
            
            # Find book
            book = db.query(Book).filter(Book.isbn == row['Book ISBN']).first()
            if not book:
                errors.append(f"Row {row_num}: Book with ISBN {row['Book ISBN']} not found")
                continue
            
            # Check if review already exists
            existing_review = db.query(Review).filter(
                Review.user_id == user.id,
                Review.book_id == book.id
            ).first()
            if existing_review:
                errors.append(f"Row {row_num}: Review already exists for this user and book")
                continue
            
            # Create review
            review = Review(
                user_id=user.id,
                book_id=book.id,
                rating=int(row['Rating']),
                title=row.get('Title', ''),
                content=row.get('Content', '')
            )
            review.update_legacy_fields()
            
            db.add(review)
            imported_count += 1
            
        except Exception as e:
            errors.append(f"Row {row_num}: {str(e)}")
    
    db.commit()
    
    return {
        "imported_count": imported_count,
        "errors": errors,
        "total_rows": row_num - 1 if 'row_num' in locals() else 0
    }
