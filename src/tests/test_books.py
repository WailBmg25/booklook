"""
Tests for book endpoints.
"""
import pytest
from faker import Faker

fake = Faker()


class TestBookListing:
    """Tests for book listing endpoint."""

    def test_get_books_success(self, client, sample_book):
        """Test getting list of books."""
        response = client.get("/books")
        
        assert response.status_code == 200
        data = response.json()
        assert "books" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["books"]) > 0

    def test_get_books_pagination(self, client, db_session, sample_author, sample_genre):
        """Test book listing pagination."""
        # Create multiple books
        from models.book_model import Book
        for i in range(15):
            book = Book(
                titre=f"Test Book {i}",
                isbn=fake.isbn13(),
                date_publication=fake.date_this_century(),
                nombre_pages=200,
                langue="English"
            )
            db_session.add(book)
        db_session.commit()
        
        # Test first page
        response = client.get("/books?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["books"]) == 10
        assert data["page"] == 1
        
        # Test second page
        response = client.get("/books?page=2&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["books"]) == 5
        assert data["page"] == 2

    def test_get_books_search(self, client, sample_book):
        """Test book search functionality."""
        search_term = sample_book.titre.split()[0]
        response = client.get(f"/books?search={search_term}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["books"]) > 0
        # Check if search term appears in any book title
        assert any(search_term.lower() in book["titre"].lower() for book in data["books"])

    def test_get_books_filter_by_genre(self, client, sample_book):
        """Test filtering books by genre."""
        genre_name = sample_book.genre_names[0] if sample_book.genre_names else None
        if not genre_name:
            pytest.skip("Sample book has no genres")
        
        response = client.get(f"/books?genre={genre_name}")
        
        assert response.status_code == 200
        data = response.json()
        # All returned books should have the genre
        for book in data["books"]:
            if book["genre_names"]:
                assert genre_name in book["genre_names"]


class TestBookDetails:
    """Tests for book details endpoint."""

    def test_get_book_by_id_success(self, client, sample_book):
        """Test getting book details by ID."""
        response = client.get(f"/books/{sample_book.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_book.id
        assert data["titre"] == sample_book.titre
        assert data["isbn"] == sample_book.isbn

    def test_get_book_nonexistent_id(self, client):
        """Test getting non-existent book returns 404."""
        response = client.get("/books/99999")
        
        assert response.status_code == 404

    def test_get_book_invalid_id(self, client):
        """Test getting book with invalid ID format."""
        response = client.get("/books/invalid")
        
        assert response.status_code == 422


class TestBookContent:
    """Tests for book content endpoints."""

    def test_get_book_page_content(self, client, sample_book_with_pages):
        """Test getting specific page content."""
        response = client.get(f"/books/{sample_book_with_pages.id}/content/page/1")
        
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "page_number" in data
        assert "total_pages" in data
        assert data["page_number"] == 1

    def test_get_book_page_out_of_range(self, client, sample_book_with_pages):
        """Test getting page number that doesn't exist."""
        response = client.get(f"/books/{sample_book_with_pages.id}/content/page/999")
        
        assert response.status_code == 404

    def test_get_book_content_no_pages(self, client, sample_book):
        """Test getting content for book with no pages."""
        response = client.get(f"/books/{sample_book.id}/content/page/1")
        
        assert response.status_code == 404


class TestBookReviews:
    """Tests for book reviews endpoint."""

    def test_get_book_reviews(self, client, sample_review):
        """Test getting reviews for a book."""
        response = client.get(f"/books/{sample_review.book_id}/reviews")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "rating" in data[0]
            assert "titre" in data[0]
            assert "contenu" in data[0]

    def test_get_reviews_for_book_without_reviews(self, client, sample_book):
        """Test getting reviews for book with no reviews."""
        response = client.get(f"/books/{sample_book.id}/reviews")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
