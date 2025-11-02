from sqlalchemy import Column, Integer, String, Text, Date, Float, Table, ForeignKey, DateTime, ARRAY, Numeric, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

# Table de liaison Many-to-Many pour Livres et Genres
book_genre_association = Table(
    'book_genre',
    Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    Column('genre_id', Integer, ForeignKey('genres.id', ondelete='CASCADE'), primary_key=True)
)

# Table de liaison Many-to-Many pour Livres et Auteurs
book_author_association = Table(
    'book_author',
    Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    Column('author_id', Integer, ForeignKey('authors.id', ondelete='CASCADE'), primary_key=True)
)

# Table de liaison pour les Favoris (User-Book)
user_favorite_association = Table(
    'user_favorites',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
    Column('book_id', Integer, ForeignKey('books.id', ondelete='CASCADE'), primary_key=True),
    Column('added_at', DateTime(timezone=True), server_default=func.now())
)


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True, index=True)
    titre = Column(String(500), nullable=False, index=True)
    isbn = Column(String(20), unique=True, nullable=False, index=True)
    date_publication = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    nombre_pages = Column(Integer, nullable=True)
    langue = Column(String(50), default="Français")
    editeur = Column(String(255), nullable=True)
    note_moyenne = Column(Float, default=0.0)
    nombre_reviews = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Enhanced fields for large dataset optimization
    author_names = Column(ARRAY(String), nullable=True, index=True)  # Denormalized author names
    genre_names = Column(ARRAY(String), nullable=True, index=True)   # Denormalized genre names
    content_path = Column(String(500), nullable=True)               # Path to book content file
    word_count = Column(Integer, nullable=True)                     # Total word count
    total_pages = Column(Integer, nullable=True)                    # Total pages for reading progress
    average_rating = Column(Numeric(3, 2), default=0)              # More precise rating (0.00-5.00)
    review_count = Column(Integer, default=0)                      # Cached review count

    # Relations
    auteurs = relationship("Author", secondary=book_author_association, back_populates="livres")
    genres = relationship("Genre", secondary=book_genre_association, back_populates="livres")
    reviews = relationship("Review", back_populates="livre", cascade="all, delete-orphan")
    favoris_par = relationship("User", secondary=user_favorite_association, back_populates="livres_favoris")

    def __repr__(self):
        return f"<Book(id={self.id}, titre='{self.titre}', isbn='{self.isbn}')>"


class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False, index=True)
    prenom = Column(String(255), nullable=True)
    biographie = Column(Text, nullable=True)
    photo_url = Column(String(500), nullable=True)
    date_naissance = Column(Date, nullable=True)
    nationalite = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    livres = relationship("Book", secondary=book_author_association, back_populates="auteurs")

    def __repr__(self):
        return f"<Author(id={self.id}, nom='{self.nom} {self.prenom}')>"


class Genre(Base):
    __tablename__ = "genres"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    livres = relationship("Book", secondary=book_genre_association, back_populates="genres")

    def __repr__(self):
        return f"<Genre(id={self.id}, nom='{self.nom}')>"


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    book_id = Column(Integer, ForeignKey('books.id', ondelete='CASCADE'), nullable=False, index=True)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Legacy fields for backward compatibility
    livre_id = Column(Integer, ForeignKey('books.id', ondelete='CASCADE'), nullable=True, index=True)
    note = Column(Integer, nullable=True)  # Maps to rating
    commentaire = Column(Text, nullable=True)  # Maps to content
    nom_utilisateur = Column(String(100), nullable=True)  # For anonymous reviews

    # Relations
    livre = relationship("Book", back_populates="reviews", foreign_keys=[livre_id])
    book = relationship("Book", foreign_keys=[book_id])
    user = relationship("User", back_populates="reviews")

    def __repr__(self):
        return f"<Review(id={self.id}, book_id={self.book_id}, rating={self.rating})>"


class ReadingProgress(Base):
    __tablename__ = "reading_progress"

    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    book_id = Column(Integer, ForeignKey('books.id', ondelete='CASCADE'), primary_key=True)
    current_page = Column(Integer, default=1)
    total_pages = Column(Integer, nullable=True)
    progress_percentage = Column(Float, default=0.0)  # 0.0 to 100.0
    last_read_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relations
    user = relationship("User", back_populates="reading_progress")
    book = relationship("Book")

    def __repr__(self):
        return f"<ReadingProgress(user_id={self.user_id}, book_id={self.book_id}, page={self.current_page})>"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Legacy fields for backward compatibility
    nom = Column(String(100), nullable=True)  # Maps to last_name
    prenom = Column(String(100), nullable=True)  # Maps to first_name
    photo_url = Column(String(500), nullable=True)

    # Relations
    livres_favoris = relationship("Book", secondary=user_favorite_association, back_populates="favoris_par")
    reviews = relationship("Review", back_populates="user", cascade="all, delete-orphan")
    reading_progress = relationship("ReadingProgress", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"