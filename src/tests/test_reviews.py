"""
Tests for review endpoints.
"""
import pytest
from faker import Faker

fake = Faker()


class TestCreateReview:
    """Tests for creating reviews."""

    def test_create_review_success(self, client, auth_headers, sample_book):
        """Test creating a review successfully."""
        review_data = {
            "book_id": sample_book.id,
            "rating": 4,
            "titre": "Great book!",
            "contenu": "I really enjoyed reading this book. Highly recommended!"
        }
        
        response = client.post(
            f"/books/{sample_book.id}/reviews",
            json=review_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["rating"] == review_data["rating"]
        assert data["titre"] == review_data["titre"]
        assert data["contenu"] == review_data["contenu"]
        assert "id" in data

    def test_create_review_unauthorized(self, client, sample_book):
        """Test creating review without authentication fails."""
        review_data = {
            "book_id": sample_book.id,
            "rating": 4,
            "titre": "Great book!",
            "contenu": "I really enjoyed reading this book."
        }
        
        response = client.post(
            f"/books/{sample_book.id}/reviews",
            json=review_data
        )
        
        assert response.status_code == 401

    def test_create_review_invalid_rating(self, client, auth_headers, sample_book):
        """Test creating review with invalid rating fails."""
        review_data = {
            "book_id": sample_book.id,
            "rating": 6,  # Invalid: should be 1-5
            "titre": "Great book!",
            "contenu": "I really enjoyed reading this book."
        }
        
        response = client.post(
            f"/books/{sample_book.id}/reviews",
            json=review_data,
            headers=auth_headers
        )
        
        assert response.status_code == 422

    def test_create_review_nonexistent_book(self, client, auth_headers):
        """Test creating review for non-existent book fails."""
        review_data = {
            "book_id": 99999,
            "rating": 4,
            "titre": "Great book!",
            "contenu": "I really enjoyed reading this book."
        }
        
        response = client.post(
            "/books/99999/reviews",
            json=review_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestGetReview:
    """Tests for getting review details."""

    def test_get_review_by_id(self, client, sample_review):
        """Test getting review by ID."""
        response = client.get(f"/reviews/{sample_review.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_review.id
        assert data["rating"] == sample_review.rating
        assert data["titre"] == sample_review.titre

    def test_get_nonexistent_review(self, client):
        """Test getting non-existent review returns 404."""
        response = client.get("/reviews/99999")
        
        assert response.status_code == 404


class TestUpdateReview:
    """Tests for updating reviews."""

    def test_update_own_review(self, client, auth_headers, sample_review, sample_user):
        """Test user can update their own review."""
        # Ensure the review belongs to the authenticated user
        sample_review.user_id = sample_user.id
        
        update_data = {
            "rating": 5,
            "titre": "Updated title",
            "contenu": "Updated content"
        }
        
        response = client.put(
            f"/reviews/{sample_review.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == update_data["rating"]
        assert data["titre"] == update_data["titre"]
        assert data["contenu"] == update_data["contenu"]

    def test_update_review_unauthorized(self, client, sample_review):
        """Test updating review without authentication fails."""
        update_data = {
            "rating": 5,
            "titre": "Updated title",
            "contenu": "Updated content"
        }
        
        response = client.put(
            f"/reviews/{sample_review.id}",
            json=update_data
        )
        
        assert response.status_code == 401


class TestDeleteReview:
    """Tests for deleting reviews."""

    def test_delete_own_review(self, client, auth_headers, db_session, sample_user, sample_book):
        """Test user can delete their own review."""
        # Create a review for the authenticated user
        from models.review_model import Review
        review = Review(
            user_id=sample_user.id,
            book_id=sample_book.id,
            rating=4,
            titre="Test review",
            contenu="Test content"
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)
        
        response = client.delete(
            f"/reviews/{review.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204

    def test_delete_review_unauthorized(self, client, sample_review):
        """Test deleting review without authentication fails."""
        response = client.delete(f"/reviews/{sample_review.id}")
        
        assert response.status_code == 401


class TestUserReviews:
    """Tests for getting user's reviews."""

    def test_get_user_reviews(self, client, auth_headers, sample_review, sample_user):
        """Test getting authenticated user's reviews."""
        # Ensure review belongs to authenticated user
        sample_review.user_id = sample_user.id
        
        response = client.get("/user/reviews", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_user_reviews_unauthorized(self, client):
        """Test getting user reviews without authentication fails."""
        response = client.get("/user/reviews")
        
        assert response.status_code == 401
