"""
Tests for authentication endpoints.
"""
import pytest
from faker import Faker

fake = Faker()


class TestUserRegistration:
    """Tests for user registration."""

    def test_register_new_user_success(self, client):
        """Test successful user registration."""
        user_data = {
            "email": fake.email(),
            "prenom": fake.first_name(),
            "nom": fake.last_name(),
            "password": "SecurePassword123!"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["prenom"] == user_data["prenom"]
        assert data["nom"] == user_data["nom"]
        assert "id" in data
        assert "mot_de_passe" not in data  # Password should not be returned

    def test_register_duplicate_email(self, client, sample_user):
        """Test registration with duplicate email fails."""
        user_data = {
            "email": sample_user.email,
            "prenom": fake.first_name(),
            "nom": fake.last_name(),
            "password": "SecurePassword123!"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client):
        """Test registration with invalid email fails."""
        user_data = {
            "email": "not-an-email",
            "prenom": fake.first_name(),
            "nom": fake.last_name(),
            "password": "SecurePassword123!"
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422  # Validation error

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields fails."""
        user_data = {
            "email": fake.email()
            # Missing prenom, nom, password
        }
        
        response = client.post("/auth/register", json=user_data)
        
        assert response.status_code == 422


class TestUserLogin:
    """Tests for user login."""

    def test_login_success(self, client, sample_user):
        """Test successful login."""
        login_data = {
            "email": sample_user.email,
            "password": "testpassword123"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == sample_user.email

    def test_login_wrong_password(self, client, sample_user):
        """Test login with wrong password fails."""
        login_data = {
            "email": sample_user.email,
            "password": "wrongpassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user fails."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "somepassword"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401

    def test_login_missing_credentials(self, client):
        """Test login with missing credentials fails."""
        response = client.post("/auth/login", json={})
        
        assert response.status_code == 422


class TestAdminLogin:
    """Tests for admin authentication."""

    def test_admin_login_success(self, client, admin_user):
        """Test successful admin login."""
        login_data = {
            "email": admin_user.email,
            "password": "adminpassword123"
        }
        
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["is_admin"] is True

    def test_non_admin_cannot_access_admin_routes(self, client, auth_headers):
        """Test that non-admin users cannot access admin routes."""
        response = client.get("/admin/users", headers=auth_headers)
        
        assert response.status_code == 403
