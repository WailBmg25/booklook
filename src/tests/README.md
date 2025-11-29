# BookLook Test Suite

This directory contains comprehensive tests for the BookLook application.

## Important Note

⚠️ **Database Compatibility**: The current test suite uses SQLite for in-memory testing, but the Book model uses PostgreSQL-specific ARRAY types for `author_names` and `genre_names` fields. This causes compatibility issues.

**Solutions:**
1. **Recommended**: Run tests against a PostgreSQL test database (see PostgreSQL Setup below)
2. **Alternative**: Tests will skip ARRAY fields when using SQLite (relationships still work)

## Setup

### Install Test Dependencies

```bash
cd src
pip install -r requirements-test.txt
```

### PostgreSQL Test Database Setup (Recommended)

For full compatibility, use a PostgreSQL test database:

```bash
# Create test database
createdb booklook_test

# Update conftest.py to use PostgreSQL:
# SQLALCHEMY_TEST_DATABASE_URL = "postgresql://user:password@localhost/booklook_test"
```

## Running Tests

### Run All Tests

```bash
cd src
pytest
```

### Run Specific Test File

```bash
cd src
pytest tests/test_auth.py
pytest tests/test_books.py
pytest tests/test_reviews.py
```

### Run Specific Test Class

```bash
cd src
pytest tests/test_auth.py::TestUserRegistration
```

### Run Specific Test Function

```bash
cd src
pytest tests/test_auth.py::TestUserRegistration::test_register_new_user_success
```

### Run with Coverage Report

```bash
cd src
pytest --cov=. --cov-report=html
```

Then open `htmlcov/index.html` in your browser to view the coverage report.

### Run with Verbose Output

```bash
cd src
pytest -v
```

### Run Tests in Parallel (faster)

```bash
cd src
pip install pytest-xdist
pytest -n auto
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures and configuration
├── test_auth.py             # Authentication tests
├── test_books.py            # Book endpoints tests
├── test_reviews.py          # Review endpoints tests
├── test_reading_progress.py # Reading progress tests
├── test_user.py             # User profile and favorites tests
└── test_admin.py            # Admin endpoints tests
```

## Test Coverage

The test suite covers:

- ✅ **Authentication**: Registration, login, admin authentication
- ✅ **Books**: Listing, search, filtering, pagination, details, content
- ✅ **Reviews**: Create, read, update, delete reviews
- ✅ **Reading Progress**: Track and update reading progress
- ✅ **User Profile**: Get and update profile, manage favorites
- ✅ **Admin**: User management, book management, review moderation, analytics

## Fixtures

Common fixtures available in `conftest.py`:

- `db_session`: Test database session
- `client`: FastAPI test client
- `sample_user`: Regular user
- `admin_user`: Admin user
- `sample_book`: Book with metadata
- `sample_book_with_pages`: Book with page content
- `sample_author`: Author
- `sample_genre`: Genre
- `sample_review`: Review
- `sample_reading_progress`: Reading progress record
- `auth_headers`: Authentication headers for regular user
- `admin_auth_headers`: Authentication headers for admin user

## Writing New Tests

### Example Test

```python
def test_my_feature(client, auth_headers, sample_book):
    """Test description."""
    response = client.get(
        f"/api/endpoint/{sample_book.id}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

### Best Practices

1. Use descriptive test names that explain what is being tested
2. Follow the Arrange-Act-Assert pattern
3. Use fixtures for common setup
4. Test both success and failure cases
5. Test edge cases and boundary conditions
6. Keep tests independent and isolated
7. Use appropriate assertions

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    cd src
    pip install -r requirements.txt
    pip install -r requirements-test.txt
    pytest --cov=. --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Troubleshooting

### Import Errors

If you get import errors, make sure you're running pytest from the `src` directory:

```bash
cd src
pytest
```

### Database Errors

Tests use an in-memory SQLite database. If you encounter database errors, ensure all models are properly imported in `conftest.py`.

### Authentication Errors

If authentication tests fail, check that:
- Password hashing is working correctly
- JWT token generation is configured
- Auth middleware is properly set up
