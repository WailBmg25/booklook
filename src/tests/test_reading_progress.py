"""
Tests for reading progress endpoints.
"""
import pytest


class TestReadingProgress:
    """Tests for reading progress tracking."""

    def test_get_reading_progress(self, client, auth_headers, sample_reading_progress, sample_user):
        """Test getting reading progress for a book."""
        # Ensure progress belongs to authenticated user
        sample_reading_progress.user_id = sample_user.id
        
        response = client.get(
            f"/user/reading-progress/{sample_reading_progress.book_id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == sample_reading_progress.book_id
        assert data["current_page"] == sample_reading_progress.current_page
        assert data["status"] == sample_reading_progress.status

    def test_get_reading_progress_not_found(self, client, auth_headers):
        """Test getting reading progress for book user hasn't started."""
        response = client.get(
            "/user/reading-progress/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404

    def test_get_reading_progress_unauthorized(self, client, sample_reading_progress):
        """Test getting reading progress without authentication fails."""
        response = client.get(
            f"/user/reading-progress/{sample_reading_progress.book_id}"
        )
        
        assert response.status_code == 401

    def test_update_reading_progress(self, client, auth_headers, sample_book_with_pages):
        """Test updating reading progress."""
        progress_data = {
            "current_page": 3,
            "status": "reading"
        }
        
        response = client.put(
            f"/user/reading-progress/{sample_book_with_pages.id}",
            json=progress_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_page"] == progress_data["current_page"]
        assert data["status"] == progress_data["status"]

    def test_update_reading_progress_creates_if_not_exists(self, client, auth_headers, sample_book_with_pages):
        """Test updating reading progress creates new record if doesn't exist."""
        progress_data = {
            "current_page": 1,
            "status": "reading"
        }
        
        response = client.put(
            f"/user/reading-progress/{sample_book_with_pages.id}",
            json=progress_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["current_page"] == progress_data["current_page"]

    def test_update_reading_progress_unauthorized(self, client, sample_book):
        """Test updating reading progress without authentication fails."""
        progress_data = {
            "current_page": 1,
            "status": "reading"
        }
        
        response = client.put(
            f"/user/reading-progress/{sample_book.id}",
            json=progress_data
        )
        
        assert response.status_code == 401


class TestReadingHistory:
    """Tests for reading history endpoints."""

    def test_get_reading_history(self, client, auth_headers, sample_reading_progress, sample_user):
        """Test getting user's reading history."""
        # Ensure progress belongs to authenticated user
        sample_reading_progress.user_id = sample_user.id
        
        response = client.get("/user/reading-history", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_reading_history_unauthorized(self, client):
        """Test getting reading history without authentication fails."""
        response = client.get("/user/reading-history")
        
        assert response.status_code == 401

    def test_get_currently_reading(self, client, auth_headers, sample_reading_progress, sample_user):
        """Test getting currently reading books."""
        # Ensure progress belongs to authenticated user and status is reading
        sample_reading_progress.user_id = sample_user.id
        sample_reading_progress.status = "reading"
        
        response = client.get("/user/currently-reading", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_currently_reading_unauthorized(self, client):
        """Test getting currently reading without authentication fails."""
        response = client.get("/user/currently-reading")
        
        assert response.status_code == 401
