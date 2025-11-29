"""
Tests for user profile and favorites endpoints.
"""
import pytest
from faker import Faker

fake = Faker()


class TestUserProfile:
    """Tests for user profile endpoints."""

    def test_get_user_profile(self, client, auth_headers, sample_user):
        """Test getting user profile."""
        response = client.get("/user/profile", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user.email
        assert data["prenom"] == sample_user.prenom
        assert data["nom"] == sample_user.nom
        assert "mot_de_passe" not in data

    def test_get_user_profile_unauthorized(self, client):
        """Test getting profile without authentication fails."""
        response = client.get("/user/profile")
        
        assert response.status_code == 401

    def test_update_user_profile(self, client, auth_headers):
        """Test updating user profile."""
        update_data = {
            "prenom": "Updated",
            "nom": "Name"
        }
        
        response = client.put(
            "/user/profile",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["prenom"] == update_data["prenom"]
        assert data["nom"] == update_data["nom"]

    def test_update_user_profile_unauthorized(self, client):
        """Test updating profile without authentication fails."""
        update_data = {
            "prenom": "Updated",
            "nom": "Name"
        }
        
        response = client.put("/user/profile", json=update_data)
        
        assert response.status_code == 401


class TestUserFavorites:
    """Tests for user favorites endpoints."""

    def test_add_favorite_book(self, client, auth_headers, sample_book):
        """Test adding a book to favorites."""
        response = client.post(
            f"/user/favorites/{sample_book.id}",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert "message" in data or "favorites" in data

    def test_add_favorite_unauthorized(self, client, sample_book):
        """Test adding favorite without authentication fails."""
        response = client.post(f"/user/favorites/{sample_book.id}")
        
        assert response.status_code == 401

    def test_add_favorite_nonexistent_book(self, client, auth_headers):
        """Test adding non-existent book to favorites fails."""
        response = client.post(
            "/user/favorites/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404

    def test_get_user_favorites(self, client, auth_headers, sample_book, db_session, sample_user):
        """Test getting user's favorite books."""
        # Add book to favorites
        sample_user.livres_favoris.append(sample_book)
        db_session.commit()
        
        response = client.get("/user/favorites", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_favorites_unauthorized(self, client):
        """Test getting favorites without authentication fails."""
        response = client.get("/user/favorites")
        
        assert response.status_code == 401

    def test_remove_favorite_book(self, client, auth_headers, sample_book, db_session, sample_user):
        """Test removing a book from favorites."""
        # Add book to favorites first
        sample_user.livres_favoris.append(sample_book)
        db_session.commit()
        
        response = client.delete(
            f"/user/favorites/{sample_book.id}",
            headers=auth_headers
        )
        
        assert response.status_code in [200, 204]

    def test_remove_favorite_unauthorized(self, client, sample_book):
        """Test removing favorite without authentication fails."""
        response = client.delete(f"/user/favorites/{sample_book.id}")
        
        assert response.status_code == 401
