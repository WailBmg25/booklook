"""
Pytest configuration and fixtures for BookLook tests.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from faker import Faker

from database import Base, get_db
from models.user_model import User
from models.book_model import Book
from models.author_model import Author
from models.genre_model import Genre
from models.review_model import Review
from models.reading_progress_model import ReadingProgress
from models.book_page_model import BookPage
from helpers.auth_helper import AuthHelper

# Initialize auth helper
auth_helper = AuthHelper()

# Initialize Faker
fake = Faker()

# Test database URL (in-memory SQLite)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session override."""
    from main import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user(db_session):
    """Create a sample user for testing."""
    user = User(
        email=fake.email(),
        prenom=fake.first_name(),
        nom=fake.last_name(),
        mot_de_passe=auth_helper.hash_password("testpassword123"),
        is_admin=False
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session):
    """Create an admin user for testing."""
    user = User(
        email="admin@booklook.com",
        prenom="Admin",
        nom="User",
        mot_de_passe=auth_helper.hash_password("adminpassword123"),
        is_admin=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_author(db_session):
    """Create a sample author for testing."""
    author = Author(
        prenom=fake.first_name(),
        nom=fake.last_name(),
        biographie=fake.text(max_nb_chars=200)
    )
    db_session.add(author)
    db_session.commit()
    db_session.refresh(author)
    return author


@pytest.fixture
def sample_genre(db_session):
    """Create a sample genre for testing."""
    genre = Genre(
        nom=fake.word().capitalize(),
        description=fake.text(max_nb_chars=100)
    )
    db_session.add(genre)
    db_session.commit()
    db_session.refresh(genre)
    return genre


@pytest.fixture
def sample_book(db_session, sample_author, sample_genre):
    """Create a sample book for testing."""
    book = Book(
        titre=fake.sentence(nb_words=4),
        isbn=fake.isbn13(),
        date_publication=fake.date_this_century(),
        nombre_pages=fake.random_int(min=100, max=500),
        langue="English",
        description=fake.text(max_nb_chars=300),
        image_url=fake.image_url()
        # Note: author_names and genre_names use ARRAY type which isn't supported in SQLite
        # These will be None in tests, but relationships will work
    )
    db_session.add(book)
    db_session.flush()
    
    # Link author and genre
    book.auteurs.append(sample_author)
    book.genres.append(sample_genre)
    
    db_session.commit()
    db_session.refresh(book)
    return book


@pytest.fixture
def sample_book_with_pages(db_session, sample_book):
    """Create a sample book with pages for testing."""
    # Add some pages to the book
    for i in range(1, 6):
        page = BookPage(
            book_id=sample_book.id,
            page_number=i,
            content=fake.text(max_nb_chars=500)
        )
        page.calculate_word_count()
        db_session.add(page)
    
    db_session.commit()
    db_session.refresh(sample_book)
    return sample_book


@pytest.fixture
def sample_review(db_session, sample_user, sample_book):
    """Create a sample review for testing."""
    review = Review(
        user_id=sample_user.id,
        book_id=sample_book.id,
        rating=fake.random_int(min=1, max=5),
        titre=fake.sentence(nb_words=5),
        contenu=fake.text(max_nb_chars=200)
    )
    db_session.add(review)
    db_session.commit()
    db_session.refresh(review)
    return review


@pytest.fixture
def sample_reading_progress(db_session, sample_user, sample_book_with_pages):
    """Create a sample reading progress for testing."""
    progress = ReadingProgress(
        user_id=sample_user.id,
        book_id=sample_book_with_pages.id,
        current_page=2,
        status="reading"
    )
    db_session.add(progress)
    db_session.commit()
    db_session.refresh(progress)
    return progress


@pytest.fixture
def auth_headers(client, sample_user):
    """Get authentication headers for a sample user."""
    response = client.post(
        "/auth/login",
        json={
            "email": sample_user.email,
            "password": "testpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(client, admin_user):
    """Get authentication headers for an admin user."""
    response = client.post(
        "/auth/login",
        json={
            "email": admin_user.email,
            "password": "adminpassword123"
        }
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
