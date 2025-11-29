"""
Tests for admin endpoints.
"""
import pytest
from faker import Faker

fake = Faker()


class TestAdminUserManagement:
    """Tests for admin user management endpoints."""

    def test_get_all_users(self, client, admin_auth_headers, sample_user):
        """Test admin can get list of all users."""
        response = client.get("/admin/users", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert isinstance(data["users"], list)

    def test_get_users_unauthorized(self, client, auth_headers):
        """Test non-admin cannot access user list."""
        response = client.get("/admin/users", headers=auth_headers)
        
        assert response.status_code == 403

    def test_suspend_user(self, client, admin_auth_headers, sample_user):
        """Test admin can suspend a user."""
        response = client.put(
            f"/admin/users/{sample_user.id}/suspend",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["statut"] == "suspended"

    def test_activate_user(self, client, admin_auth_headers, sample_user, db_session):
        """Test admin can activate a suspended user."""
        # Suspend user first
        sample_user.statut = "suspended"
        db_session.commit()
        
        response = client.put(
            f"/admin/users/{sample_user.id}/activate",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["statut"] == "active"

    def test_delete_user(self, client, admin_auth_headers, db_session):
        """Test admin can delete a user."""
        # Create a user to delete
        from models.user_model import User
        from helpers.auth_helper import AuthHelper
        
        auth_helper = AuthHelper()
        user = User(
            email=fake.email(),
            prenom=fake.first_name(),
            nom=fake.last_name(),
            mot_de_passe=auth_helper.hash_password("password123")
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        
        response = client.delete(
            f"/admin/users/{user.id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 204


class TestAdminBookManagement:
    """Tests for admin book management endpoints."""

    def test_create_book(self, client, admin_auth_headers):
        """Test admin can create a new book."""
        book_data = {
            "titre": fake.sentence(nb_words=4),
            "isbn": fake.isbn13(),
            "date_publication": "2023-01-01",
            "nombre_pages": 300,
            "langue": "English",
            "description": fake.text(max_nb_chars=200)
        }
        
        response = client.post(
            "/admin/books",
            json=book_data,
            headers=admin_auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["titre"] == book_data["titre"]
        assert data["isbn"] == book_data["isbn"]

    def test_create_book_unauthorized(self, client, auth_headers):
        """Test non-admin cannot create books."""
        book_data = {
            "titre": "Test Book",
            "isbn": fake.isbn13(),
            "nombre_pages": 300,
            "langue": "English"
        }
        
        response = client.post(
            "/admin/books",
            json=book_data,
            headers=auth_headers
        )
        
        assert response.status_code == 403

    def test_update_book(self, client, admin_auth_headers, sample_book):
        """Test admin can update a book."""
        update_data = {
            "titre": "Updated Title",
            "description": "Updated description"
        }
        
        response = client.put(
            f"/admin/books/{sample_book.id}",
            json=update_data,
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["titre"] == update_data["titre"]

    def test_delete_book(self, client, admin_auth_headers, db_session):
        """Test admin can delete a book."""
        # Create a book to delete
        from models.book_model import Book
        
        book = Book(
            titre="Book to Delete",
            isbn=fake.isbn13(),
            nombre_pages=200,
            langue="English"
        )
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)
        
        response = client.delete(
            f"/admin/books/{book.id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 204


class TestAdminReviewModeration:
    """Tests for admin review moderation endpoints."""

    def test_get_all_reviews(self, client, admin_auth_headers, sample_review):
        """Test admin can get all reviews."""
        response = client.get("/admin/reviews", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "reviews" in data
        assert isinstance(data["reviews"], list)

    def test_get_reviews_unauthorized(self, client, auth_headers):
        """Test non-admin cannot access all reviews."""
        response = client.get("/admin/reviews", headers=auth_headers)
        
        assert response.status_code == 403

    def test_delete_review(self, client, admin_auth_headers, sample_review):
        """Test admin can delete any review."""
        response = client.delete(
            f"/admin/reviews/{sample_review.id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 204

    def test_flag_review(self, client, admin_auth_headers, sample_review):
        """Test admin can flag a review."""
        response = client.put(
            f"/admin/reviews/{sample_review.id}/flag",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200


class TestAdminAnalytics:
    """Tests for admin analytics endpoints."""

    def test_get_analytics_overview(self, client, admin_auth_headers):
        """Test admin can get analytics overview."""
        response = client.get("/admin/analytics/overview", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "total_books" in data
        assert "total_users" in data
        assert "total_reviews" in data

    def test_get_analytics_unauthorized(self, client, auth_headers):
        """Test non-admin cannot access analytics."""
        response = client.get("/admin/analytics/overview", headers=auth_headers)
        
        assert response.status_code == 403

    def test_get_user_analytics(self, client, admin_auth_headers):
        """Test admin can get user analytics."""
        response = client.get("/admin/analytics/users", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_book_analytics(self, client, admin_auth_headers):
        """Test admin can get book analytics."""
        response = client.get("/admin/analytics/books", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
