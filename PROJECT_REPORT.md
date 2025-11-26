# BookLook - Comprehensive Project Report

## Executive Summary

BookLook is a high-performance web application for browsing, reading, and reviewing books from large datasets (>300GB). Built with FastAPI (Python), PostgreSQL, Redis, and Next.js, it supports concurrent users, real-time search, and smooth reading experiences.

**Key Features:**
- Browse and search large book collections
- Smooth scrolling reading interface with progress tracking
- User reviews and ratings with sentiment analysis
- Favorites and reading history management
- Admin dashboard for content moderation
- High availability with database replication and caching

**Technology Stack:**
- Backend: Python 3.13+, FastAPI, SQLAlchemy, PostgreSQL 15, Redis 7
- Frontend: Next.js 14, Tailwind CSS, NextAuth.js
- Deployment: Docker, Nginx load balancer
- Architecture: MVC pattern with repository layer

---

## Table of Contents

1. [System Architecture](#system-architecture)
2. [Database Design](#database-design)
3. [Class Diagrams](#class-diagrams)
4. [Use Case Diagrams](#use-case-diagrams)
5. [Sequence Diagrams](#sequence-diagrams)
6. [Component Diagrams](#component-diagrams)
7. [Deployment Architecture](#deployment-architecture)
8. [API Documentation](#api-documentation)
9. [Data Loading Guide](#data-loading-guide)

---

## 1. System Architecture

### High-Level Architecture Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        WEB[Web Browser]
        MOBILE[Mobile Browser]
    end

    subgraph "Load Balancer"
        LB[Nginx Load Balancer]
    end

    subgraph "Frontend Layer"
        UI[Next.js Application]
        AUTH[NextAuth Authentication]
    end

    subgraph "Backend API Layer"
        API1[FastAPI Instance 1]
        API2[FastAPI Instance 2]
        API3[FastAPI Instance N]
    end

    subgraph "Caching Layer"
        REDIS_M[Redis Master]
        REDIS_S[Redis Replicas]
    end

    subgraph "Database Layer"
        PG_M[(PostgreSQL Master)]
        PG_R1[(Read Replica 1)]
        PG_R2[(Read Replica 2)]
    end

    subgraph "Storage Layer"
        FS[File Storage - Book Content]
    end

    WEB --> LB
    MOBILE --> LB
    LB --> UI
    UI --> AUTH
    UI --> API1
    UI --> API2
    UI --> API3
    
    API1 --> REDIS_M
    API2 --> REDIS_M
    API3 --> REDIS_M
    REDIS_M --> REDIS_S
    
    API1 --> PG_M
    API1 --> PG_R1
    API2 --> PG_R2
    API3 --> PG_M
    
    API1 --> FS
    API2 --> FS
    API3 --> FS
    
    PG_M -.Replication.-> PG_R1
    PG_M -.Replication.-> PG_R2
```

### MVC Architecture Pattern

```mermaid
graph LR
    subgraph "Presentation Layer"
        ROUTES[FastAPI Routes]
    end
    
    subgraph "Business Logic Layer"
        CONTROLLERS[Controllers]
    end
    
    subgraph "Data Access Layer"
        REPOS[Repositories]
    end
    
    subgraph "Domain Layer"
        MODELS[Models]
    end
    
    subgraph "Infrastructure"
        DB[(PostgreSQL)]
        CACHE[(Redis)]
    end
    
    ROUTES --> CONTROLLERS
    CONTROLLERS --> REPOS
    REPOS --> MODELS
    MODELS --> DB
    CONTROLLERS --> CACHE
```

---

## 2. Database Design

### Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    USERS ||--o{ REVIEWS : writes
    USERS ||--o{ READING_PROGRESS : tracks
    USERS }o--o{ BOOKS : favorites
    
    BOOKS ||--o{ REVIEWS : receives
    BOOKS ||--o{ READING_PROGRESS : has
    BOOKS }o--o{ AUTHORS : written_by
    BOOKS }o--o{ GENRES : categorized_as
    
    USERS {
        int id PK
        string email UK
        string first_name
        string last_name
        string password_hash
        boolean is_active
        boolean is_admin
        timestamp created_at
        timestamp updated_at
    }
    
    BOOKS {
        int id PK
        string titre
        string isbn UK
        date date_publication
        text description
        string image_url
        int nombre_pages
        string langue
        string editeur
        float note_moyenne
        int nombre_reviews
        array author_names
        array genre_names
        string content_path
        int word_count
        int total_pages
        decimal average_rating
        int review_count
        timestamp created_at
        timestamp updated_at
    }
    
    AUTHORS {
        int id PK
        string nom
        string prenom
        text biographie
        string photo_url
        date date_naissance
        string nationalite
        timestamp created_at
    }
    
    GENRES {
        int id PK
        string nom UK
        text description
        timestamp created_at
    }
    
    REVIEWS {
        int id PK
        int user_id FK
        int book_id FK
        int rating
        string title
        text content
        boolean is_flagged
        timestamp created_at
        timestamp updated_at
    }
    
    READING_PROGRESS {
        int user_id PK,FK
        int book_id PK,FK
        int current_page
        int total_pages
        float progress_percentage
        timestamp last_read_at
        timestamp created_at
        timestamp updated_at
    }
    
    BOOK_AUTHOR {
        int book_id PK,FK
        int author_id PK,FK
    }
    
    BOOK_GENRE {
        int book_id PK,FK
        int genre_id PK,FK
    }
    
    USER_FAVORITES {
        int user_id PK,FK
        int book_id PK,FK
        timestamp added_at
    }
```

### Database Schema SQL

```sql
-- Users Table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_users_email ON users(email);

-- Authors Table
CREATE TABLE authors (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(255) NOT NULL,
    prenom VARCHAR(255),
    biographie TEXT,
    photo_url VARCHAR(500),
    date_naissance DATE,
    nationalite VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_authors_nom ON authors(nom);

-- Genres Table
CREATE TABLE genres (
    id SERIAL PRIMARY KEY,
    nom VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_genres_nom ON genres(nom);

-- Books Table (Optimized for large datasets)
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    titre VARCHAR(500) NOT NULL,
    isbn VARCHAR(20) UNIQUE NOT NULL,
    date_publication DATE,
    description TEXT,
    image_url VARCHAR(500),
    nombre_pages INTEGER,
    langue VARCHAR(50) DEFAULT 'Français',
    editeur VARCHAR(255),
    note_moyenne FLOAT DEFAULT 0.0,
    nombre_reviews INTEGER DEFAULT 0,
    author_names TEXT[],  -- Denormalized for performance
    genre_names TEXT[],   -- Denormalized for performance
    content_path VARCHAR(500),
    word_count INTEGER,
    total_pages INTEGER,
    average_rating NUMERIC(3,2) DEFAULT 0,
    review_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Performance indexes
CREATE INDEX idx_books_titre ON books(titre);
CREATE INDEX idx_books_isbn ON books(isbn);
CREATE INDEX idx_books_titre_gin ON books USING gin(to_tsvector('english', titre));
CREATE INDEX idx_books_authors_gin ON books USING gin(author_names);
CREATE INDEX idx_books_genres_gin ON books USING gin(genre_names);
CREATE INDEX idx_books_rating ON books(average_rating DESC);
CREATE INDEX idx_books_publication ON books(date_publication);

-- Reviews Table
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(200),
    content TEXT,
    is_flagged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id, book_id)  -- One review per user per book
);

CREATE INDEX idx_reviews_user ON reviews(user_id);
CREATE INDEX idx_reviews_book ON reviews(book_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);

-- Reading Progress Table
CREATE TABLE reading_progress (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    current_page INTEGER DEFAULT 1,
    total_pages INTEGER,
    progress_percentage FLOAT DEFAULT 0.0,
    last_read_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    PRIMARY KEY (user_id, book_id)
);

CREATE INDEX idx_reading_progress_user ON reading_progress(user_id);
CREATE INDEX idx_reading_progress_last_read ON reading_progress(last_read_at DESC);

-- Many-to-Many: Books and Authors
CREATE TABLE book_author (
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, author_id)
);

CREATE INDEX idx_book_author_book ON book_author(book_id);
CREATE INDEX idx_book_author_author ON book_author(author_id);

-- Many-to-Many: Books and Genres
CREATE TABLE book_genre (
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    genre_id INTEGER NOT NULL REFERENCES genres(id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, genre_id)
);

CREATE INDEX idx_book_genre_book ON book_genre(book_id);
CREATE INDEX idx_book_genre_genre ON book_genre(genre_id);

-- Many-to-Many: User Favorites
CREATE TABLE user_favorites (
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    book_id INTEGER NOT NULL REFERENCES books(id) ON DELETE CASCADE,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (user_id, book_id)
);

CREATE INDEX idx_user_favorites_user ON user_favorites(user_id);
CREATE INDEX idx_user_favorites_book ON user_favorites(book_id);
```

---

## 3. Class Diagrams

### Domain Models Class Diagram

```mermaid
classDiagram
    class User {
        +int id
        +string email
        +string first_name
        +string last_name
        +string password_hash
        +boolean is_active
        +boolean is_admin
        +datetime created_at
        +datetime updated_at
        +get_full_name() string
        +get_display_name() string
        +is_book_favorited(book_id) boolean
        +add_favorite_book(book) boolean
        +remove_favorite_book(book) boolean
        +get_favorites_count() int
        +get_reviews_count() int
        +has_reviewed_book(book_id) boolean
        +get_average_rating_given() float
        +is_active_reviewer() boolean
        +get_reading_progress_count() int
        +get_finished_books_count() int
        +get_completion_rate() float
        +to_dict() dict
    }
    
    class Book {
        +int id
        +string titre
        +string isbn
        +date date_publication
        +text description
        +string image_url
        +int nombre_pages
        +string langue
        +string editeur
        +array author_names
        +array genre_names
        +string content_path
        +int word_count
        +int total_pages
        +decimal average_rating
        +int review_count
        +datetime created_at
        +datetime updated_at
        +update_rating_stats(avg, count) void
        +calculate_progress_percentage(page) float
        +get_display_title() string
        +get_author_display() string
        +get_genre_display() string
        +is_highly_rated() boolean
        +has_sufficient_reviews() boolean
        +get_publication_year() int
        +is_recent_publication() boolean
        +get_reading_difficulty() string
        +get_estimated_reading_time() int
        +update_denormalized_fields() void
        +to_dict() dict
    }
    
    class Author {
        +int id
        +string nom
        +string prenom
        +text biographie
        +string photo_url
        +date date_naissance
        +string nationalite
        +datetime created_at
        +get_full_name() string
        +get_display_name() string
        +get_books_count() int
        +is_prolific_author() boolean
        +get_age() int
        +has_biography() boolean
        +get_biography_preview() string
        +to_dict() dict
    }
    
    class Genre {
        +int id
        +string nom
        +text description
        +datetime created_at
        +get_display_name() string
        +get_books_count() int
        +is_popular_genre() boolean
        +has_description() boolean
        +get_description_preview() string
        +get_average_rating() float
        +get_top_rated_books() list
        +to_dict() dict
    }
    
    class Review {
        +int id
        +int user_id
        +int book_id
        +int rating
        +string title
        +text content
        +boolean is_flagged
        +datetime created_at
        +datetime updated_at
        +is_valid_rating() boolean
        +get_rating_stars() string
        +is_positive_review() boolean
        +is_negative_review() boolean
        +is_neutral_review() boolean
        +has_content() boolean
        +has_title() boolean
        +get_content_preview() string
        +get_display_title() string
        +is_recent() boolean
        +get_sentiment() string
        +get_word_count() int
        +is_detailed_review() boolean
        +to_dict() dict
    }
    
    class ReadingProgress {
        +int user_id
        +int book_id
        +int current_page
        +int total_pages
        +float progress_percentage
        +datetime last_read_at
        +datetime created_at
        +datetime updated_at
        +calculate_progress_percentage() float
        +is_finished() boolean
        +is_started() boolean
        +is_in_progress() boolean
        +is_not_started() boolean
        +get_pages_remaining() int
        +get_pages_read() int
        +get_progress_status() string
        +get_progress_category() string
        +get_estimated_time_remaining() int
        +update_reading_position(page) void
        +mark_as_finished() void
        +reset_progress() void
        +is_recently_read() boolean
        +get_reading_streak_days() int
        +get_reading_velocity() float
        +to_dict() dict
    }
    
    User "1" --> "*" Review : writes
    User "1" --> "*" ReadingProgress : tracks
    User "*" --> "*" Book : favorites
    Book "1" --> "*" Review : receives
    Book "1" --> "*" ReadingProgress : has
    Book "*" --> "*" Author : written_by
    Book "*" --> "*" Genre : categorized_as
```

### Repository Layer Class Diagram

```mermaid
classDiagram
    class BaseRepository {
        <<abstract>>
        #Session db
        +__init__(db)
        +get_by_id(id) Model
        +get_all(skip, limit) List~Model~
        +create(data) Model
        +update(id, data) Model
        +delete(id) boolean
        +count() int
    }
    
    class BookRepository {
        +find_by_title(title) List~Book~
        +find_by_isbn(isbn) Book
        +find_by_genre(genres) List~Book~
        +find_by_author(authors) List~Book~
        +search_books(query) List~Book~
        +get_highly_rated(min_rating) List~Book~
        +get_recent_books(days) List~Book~
        +update_rating_stats(book_id, avg, count) void
        +get_books_paginated(page, size, filters) PaginatedResult
    }
    
    class UserRepository {
        +find_by_email(email) User
        +create_user(user_data) User
        +update_user(user_id, data) User
        +get_user_favorites(user_id) List~Book~
        +add_favorite(user_id, book_id) boolean
        +remove_favorite(user_id, book_id) boolean
        +is_favorite(user_id, book_id) boolean
    }
    
    class ReviewRepository {
        +get_book_reviews(book_id) List~Review~
        +get_user_reviews(user_id) List~Review~
        +create_review(review_data) Review
        +update_review(review_id, data) Review
        +delete_review(review_id) boolean
        +get_average_rating(book_id) float
        +user_has_reviewed(user_id, book_id) boolean
    }
    
    class ReadingProgressRepository {
        +get_user_progress(user_id) List~ReadingProgress~
        +get_book_progress(user_id, book_id) ReadingProgress
        +update_progress(user_id, book_id, page) ReadingProgress
        +mark_finished(user_id, book_id) ReadingProgress
        +reset_progress(user_id, book_id) ReadingProgress
        +get_recently_read(user_id, days) List~ReadingProgress~
    }
    
    class AuthorRepository {
        +find_by_name(name) List~Author~
        +get_author_books(author_id) List~Book~
        +get_prolific_authors(min_books) List~Author~
    }
    
    class GenreRepository {
        +find_by_name(name) Genre
        +get_genre_books(genre_id) List~Book~
        +get_popular_genres(min_books) List~Genre~
    }
    
    BaseRepository <|-- BookRepository
    BaseRepository <|-- UserRepository
    BaseRepository <|-- ReviewRepository
    BaseRepository <|-- ReadingProgressRepository
    BaseRepository <|-- AuthorRepository
    BaseRepository <|-- GenreRepository
```

### Controller Layer Class Diagram

```mermaid
classDiagram
    class BookController {
        -BookRepository book_repo
        -CacheHelper cache
        +__init__(db)
        +get_books_paginated(page, size, filters) PaginatedBooks
        +get_book_details(book_id) BookDetails
        +search_books(query) List~Book~
        +get_book_content(book_id, page) BookContent
        +get_highly_rated_books(min_rating) List~Book~
        +get_recent_books() List~Book~
    }
    
    class UserController {
        -UserRepository user_repo
        -AuthHelper auth
        +__init__(db)
        +register_user(user_data) User
        +authenticate_user(email, password) Token
        +get_user_profile(user_id) UserProfile
        +update_user_profile(user_id, data) User
        +get_user_favorites(user_id) List~Book~
        +add_favorite(user_id, book_id) boolean
        +remove_favorite(user_id, book_id) boolean
    }
    
    class ReviewController {
        -ReviewRepository review_repo
        -BookRepository book_repo
        +__init__(db)
        +create_review(user_id, book_id, review_data) Review
        +get_book_reviews(book_id) List~Review~
        +get_user_reviews(user_id) List~Review~
        +update_review(review_id, data) Review
        +delete_review(review_id) boolean
        +calculate_book_rating(book_id) RatingStats
    }
    
    class ReadingProgressController {
        -ReadingProgressRepository progress_repo
        +__init__(db)
        +get_user_progress(user_id) List~ReadingProgress~
        +update_progress(user_id, book_id, page) ReadingProgress
        +mark_finished(user_id, book_id) ReadingProgress
        +get_reading_stats(user_id) ReadingStats
    }
```

---

## 4. Use Case Diagrams

### User Management Use Cases

```mermaid
graph TB
    subgraph "User Management"
        U1[Register Account]
        U2[Login]
        U3[Logout]
        U4[Update Profile]
        U5[View Profile]
    end
    
    subgraph "Actors"
        GUEST[Guest User]
        USER[Registered User]
    end
    
    GUEST --> U1
    GUEST --> U2
    USER --> U3
    USER --> U4
    USER --> U5
```

### Book Browsing Use Cases

```mermaid
graph TB
    subgraph "Book Discovery"
        B1[Browse Books]
        B2[Search Books]
        B3[Filter by Genre]
        B4[Filter by Author]
        B5[Filter by Rating]
        B6[View Book Details]
        B7[Read Book Content]
    end
    
    subgraph "Actors"
        USER[User]
    end
    
    USER --> B1
    USER --> B2
    B1 --> B3
    B1 --> B4
    B1 --> B5
    B2 --> B6
    B6 --> B7
```

### Review Management Use Cases

```mermaid
graph TB
    subgraph "Review System"
        R1[View Reviews]
        R2[Write Review]
        R3[Edit Review]
        R4[Delete Review]
        R5[Rate Book]
    end
    
    subgraph "Actors"
        USER[Registered User]
        ADMIN[Administrator]
    end
    
    USER --> R1
    USER --> R2
    USER --> R3
    USER --> R4
    USER --> R5
    ADMIN --> R1
```

### Reading Progress Use Cases

```mermaid
graph TB
    subgraph "Reading Features"
        RP1[Start Reading]
        RP2[Update Progress]
        RP3[Mark as Finished]
        RP4[View Reading History]
        RP5[Track Progress]
        RP6[Resume Reading]
    end
    
    subgraph "Actors"
        USER[Registered User]
    end
    
    USER --> RP1
    USER --> RP2
    USER --> RP3
    USER --> RP4
    USER --> RP5
    USER --> RP6
```

### Favorites Management Use Cases

```mermaid
graph TB
    subgraph "Favorites"
        F1[Add to Favorites]
        F2[Remove from Favorites]
        F3[View Favorites List]
        F4[Check if Favorited]
    end
    
    subgraph "Actors"
        USER[Registered User]
    end
    
    USER --> F1
    USER --> F2
    USER --> F3
    USER --> F4
```

### Admin Use Cases

```mermaid
graph TB
    subgraph "Administration"
        A1[Manage Books]
        A2[Manage Users]
        A3[Moderate Reviews]
        A4[View Analytics]
        A5[System Configuration]
    end
    
    subgraph "Actors"
        ADMIN[Administrator]
    end
    
    ADMIN --> A1
    ADMIN --> A2
    ADMIN --> A3
    ADMIN --> A4
    ADMIN --> A5
```

---

## 5. Sequence Diagrams

### User Registration Sequence

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Controller
    participant Repository
    participant Database
    
    Client->>API: POST /auth/register
    API->>Controller: register_user(user_data)
    Controller->>Controller: validate_email(email)
    Controller->>Controller: hash_password(password)
    Controller->>Repository: create_user(user_data)
    Repository->>Database: INSERT INTO users
    Database-->>Repository: user_id
    Repository-->>Controller: User object
    Controller-->>API: User response
    API-->>Client: 201 Created + User data
```

### User Login Sequence

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Controller
    participant Repository
    participant Database
    participant Cache
    
    Client->>API: POST /auth/login
    API->>Controller: authenticate_user(email, password)
    Controller->>Repository: find_by_email(email)
    Repository->>Database: SELECT * FROM users WHERE email=?
    Database-->>Repository: User data
    Repository-->>Controller: User object
    Controller->>Controller: verify_password(password, hash)
    Controller->>Controller: generate_token(user_id)
    Controller->>Cache: store_session(token, user_id)
    Cache-->>Controller: OK
    Controller-->>API: Token + User data
    API-->>Client: 200 OK + Token
```

### Book Search Sequence

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Controller
    participant Cache
    participant Repository
    participant Database
    
    Client->>API: GET /books?search=python&genre=tech
    API->>Controller: get_books_paginated(filters)
    Controller->>Cache: get_cached_results(cache_key)
    Cache-->>Controller: null (cache miss)
    Controller->>Repository: find_books(filters)
    Repository->>Database: SELECT * FROM books WHERE...
    Database-->>Repository: Book records
    Repository-->>Controller: List of Books
    Controller->>Cache: cache_results(cache_key, books)
    Cache-->>Controller: OK
    Controller-->>API: Paginated books
    API-->>Client: 200 OK + Books data
```

### Create Review Sequence

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Controller
    participant ReviewRepo
    participant BookRepo
    participant Database
    participant Cache
    
    Client->>API: POST /books/123/reviews
    API->>API: verify_auth_token()
    API->>Controller: create_review(user_id, book_id, data)
    Controller->>ReviewRepo: user_has_reviewed(user_id, book_id)
    ReviewRepo->>Database: SELECT * FROM reviews WHERE...
    Database-->>ReviewRepo: null (no existing review)
    ReviewRepo-->>Controller: false
    Controller->>ReviewRepo: create_review(review_data)
    ReviewRepo->>Database: INSERT INTO reviews
    Database-->>ReviewRepo: review_id
    ReviewRepo-->>Controller: Review object
    Controller->>Controller: calculate_book_rating(book_id)
    Controller->>BookRepo: update_rating_stats(book_id, avg, count)
    BookRepo->>Database: UPDATE books SET average_rating=...
    Database-->>BookRepo: OK
    BookRepo-->>Controller: OK
    Controller->>Cache: invalidate_book_cache(book_id)
    Cache-->>Controller: OK
    Controller-->>API: Review response
    API-->>Client: 201 Created + Review data
```

### Reading Progress Update Sequence

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Controller
    participant Repository
    participant Database
    
    Client->>API: PUT /user/reading-progress/123
    API->>API: verify_auth_token()
    API->>Controller: update_progress(user_id, book_id, page)
    Controller->>Repository: get_book_progress(user_id, book_id)
    Repository->>Database: SELECT * FROM reading_progress WHERE...
    Database-->>Repository: Progress record
    Repository-->>Controller: ReadingProgress object
    Controller->>Controller: calculate_progress_percentage(page)
    Controller->>Repository: update_progress(progress_data)
    Repository->>Database: UPDATE reading_progress SET...
    Database-->>Repository: OK
    Repository-->>Controller: Updated ReadingProgress
    Controller-->>API: Progress response
    API-->>Client: 200 OK + Progress data
```

### Add to Favorites Sequence

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant Controller
    participant Repository
    participant Database
    participant Cache
    
    Client->>API: POST /user/favorites/123
    API->>API: verify_auth_token()
    API->>Controller: add_favorite(user_id, book_id)
    Controller->>Repository: is_favorite(user_id, book_id)
    Repository->>Database: SELECT * FROM user_favorites WHERE...
    Database-->>Repository: null (not favorited)
    Repository-->>Controller: false
    Controller->>Repository: add_favorite(user_id, book_id)
    Repository->>Database: INSERT INTO user_favorites
    Database-->>Repository: OK
    Repository-->>Controller: true
    Controller->>Cache: invalidate_user_favorites(user_id)
    Cache-->>Controller: OK
    Controller-->>API: Success response
    API-->>Client: 201 Created
```

---

## 6. Component Diagrams

### Backend Components

```mermaid
graph TB
    subgraph "API Layer"
        ROUTES[FastAPI Routes]
        MIDDLEWARE[Middleware]
        AUTH_MW[Auth Middleware]
    end
    
    subgraph "Business Logic"
        BOOK_CTRL[Book Controller]
        USER_CTRL[User Controller]
        REVIEW_CTRL[Review Controller]
        PROGRESS_CTRL[Progress Controller]
    end
    
    subgraph "Data Access"
        BOOK_REPO[Book Repository]
        USER_REPO[User Repository]
        REVIEW_REPO[Review Repository]
        PROGRESS_REPO[Progress Repository]
    end
    
    subgraph "Domain Models"
        BOOK_MODEL[Book Model]
        USER_MODEL[User Model]
        REVIEW_MODEL[Review Model]
        PROGRESS_MODEL[Progress Model]
    end
    
    subgraph "Infrastructure"
        DB[PostgreSQL]
        CACHE[Redis]
        FILE_STORAGE[File Storage]
    end
    
    subgraph "Helpers"
        AUTH_HELPER[Auth Helper]
        CACHE_HELPER[Cache Helper]
        VALIDATION[Validation Helper]
        CONFIG[Config]
    end
    
    ROUTES --> MIDDLEWARE
    MIDDLEWARE --> AUTH_MW
    ROUTES --> BOOK_CTRL
    ROUTES --> USER_CTRL
    ROUTES --> REVIEW_CTRL
    ROUTES --> PROGRESS_CTRL
    
    BOOK_CTRL --> BOOK_REPO
    USER_CTRL --> USER_REPO
    REVIEW_CTRL --> REVIEW_REPO
    PROGRESS_CTRL --> PROGRESS_REPO
    
    BOOK_REPO --> BOOK_MODEL
    USER_REPO --> USER_MODEL
    REVIEW_REPO --> REVIEW_MODEL
    PROGRESS_REPO --> PROGRESS_MODEL
    
    BOOK_MODEL --> DB
    USER_MODEL --> DB
    REVIEW_MODEL --> DB
    PROGRESS_MODEL --> DB
    
    BOOK_CTRL --> CACHE_HELPER
    USER_CTRL --> AUTH_HELPER
    REVIEW_CTRL --> CACHE_HELPER
    
    CACHE_HELPER --> CACHE
    AUTH_HELPER --> CACHE
    BOOK_CTRL --> FILE_STORAGE
```

### Frontend Components

```mermaid
graph TB
    subgraph "Pages"
        HOME[Home Page]
        BOOK_DETAIL[Book Detail Page]
        READER[Reader Page]
        PROFILE[Profile Page]
        LOGIN[Login Page]
    end
    
    subgraph "Components"
        BOOK_TABLE[Books Table]
        BOOK_CARD[Book Card]
        FILTERS[Filter Panel]
        REVIEW_LIST[Review List]
        REVIEW_FORM[Review Form]
        PROGRESS_BAR[Progress Bar]
        READER_UI[Reader Interface]
    end
    
    subgraph "Services"
        API_CLIENT[API Client]
        AUTH_SERVICE[Auth Service]
    end
    
    subgraph "State Management"
        USER_STATE[User State]
        BOOK_STATE[Book State]
    end
    
    HOME --> BOOK_TABLE
    HOME --> FILTERS
    BOOK_TABLE --> BOOK_CARD
    
    BOOK_DETAIL --> BOOK_CARD
    BOOK_DETAIL --> REVIEW_LIST
    BOOK_DETAIL --> REVIEW_FORM
    BOOK_DETAIL --> PROGRESS_BAR
    
    READER --> READER_UI
    READER --> PROGRESS_BAR
    
    BOOK_TABLE --> API_CLIENT
    REVIEW_FORM --> API_CLIENT
    READER_UI --> API_CLIENT
    
    LOGIN --> AUTH_SERVICE
    AUTH_SERVICE --> API_CLIENT
    
    API_CLIENT --> USER_STATE
    API_CLIENT --> BOOK_STATE
```

---

## 7. Deployment Architecture

### Docker Deployment Diagram

```mermaid
graph TB
    subgraph "Docker Host"
        subgraph "Load Balancer Container"
            NGINX[Nginx:alpine]
        end
        
        subgraph "Frontend Containers"
            NEXT1[Next.js App 1]
            NEXT2[Next.js App 2]
        end
        
        subgraph "Backend Containers"
            API1[FastAPI 1]
            API2[FastAPI 2]
            API3[FastAPI 3]
        end
        
        subgraph "Database Containers"
            PG_MASTER[PostgreSQL Master]
            PG_REPLICA[PostgreSQL Replica]
        end
        
        subgraph "Cache Containers"
            REDIS_M[Redis Master]
            REDIS_S[Redis Slave]
        end
        
        subgraph "Storage"
            VOLUMES[Docker Volumes]
        end
    end
    
    NGINX --> NEXT1
    NGINX --> NEXT2
    NEXT1 --> API1
    NEXT1 --> API2
    NEXT2 --> API2
    NEXT2 --> API3
    
    API1 --> PG_MASTER
    API2 --> PG_REPLICA
    API3 --> PG_MASTER
    
    API1 --> REDIS_M
    API2 --> REDIS_M
    API3 --> REDIS_M
    
    PG_MASTER --> VOLUMES
    PG_REPLICA --> VOLUMES
    REDIS_M --> VOLUMES
```

### Network Architecture

```mermaid
graph TB
    subgraph "Public Network"
        INTERNET[Internet]
        CDN[CDN - Static Assets]
    end
    
    subgraph "DMZ"
        LB[Load Balancer]
        WAF[Web Application Firewall]
    end
    
    subgraph "Application Network"
        WEB[Web Servers]
        API[API Servers]
    end
    
    subgraph "Data Network"
        DB[Database Cluster]
        CACHE[Cache Cluster]
        STORAGE[File Storage]
    end
    
    INTERNET --> CDN
    INTERNET --> WAF
    WAF --> LB
    LB --> WEB
    WEB --> API
    API --> DB
    API --> CACHE
    API --> STORAGE
```

---

## 8. API Documentation

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | Login user | No |
| POST | `/auth/logout` | Logout user | Yes |

### Book Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/books` | List books with pagination | No |
| GET | `/books/{id}` | Get book details | No |
| GET | `/books/{id}/content` | Get book content | No |
| GET | `/books/{id}/reviews` | Get book reviews | No |

### Review Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/books/{id}/reviews` | Create review | Yes |
| GET | `/reviews/{id}` | Get review | No |
| PUT | `/reviews/{id}` | Update review | Yes |
| DELETE | `/reviews/{id}` | Delete review | Yes |

### User Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/user/profile` | Get user profile | Yes |
| PUT | `/user/profile` | Update profile | Yes |
| GET | `/user/favorites` | Get favorites | Yes |
| POST | `/user/favorites/{book_id}` | Add favorite | Yes |
| DELETE | `/user/favorites/{book_id}` | Remove favorite | Yes |

### Reading Progress Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/user/reading-progress` | Get all progress | Yes |
| GET | `/user/reading-progress/{book_id}` | Get book progress | Yes |
| PUT | `/user/reading-progress/{book_id}` | Update progress | Yes |

---

## 9. Data Loading Guide

### Database Setup

#### Step 1: Start Docker Services

```bash
cd docker
docker-compose up -d
```

This starts:
- PostgreSQL on port 5432
- Redis on port 6379
- pgAdmin on port 5050 (optional)

#### Step 2: Run Database Migrations

```bash
cd src
alembic upgrade head
```

This creates all tables with proper indexes and constraints.

### Data Loading Scripts

#### Load Sample Data

```bash
python add_sample_data.py
```

This script loads:
- 10 sample users
- 50 sample books
- 20 sample authors
- 10 sample genres
- 100 sample reviews
- Sample reading progress records

### Institutional Books Dataset Integration

#### Dataset Structure Expected

```
/data
  /institutional_books
    - books.csv (or books.json)
    - authors.csv
    - genres.csv
    /content
      /book_1
        - page_001.txt
        - page_002.txt
        ...
      /book_2
        ...
```

#### CSV Format for Books

```csv
id,title,isbn,publication_date,description,image_url,pages,language,publisher,author_names,genre_names,content_path,word_count
1,"Python Programming","978-0-123456-78-9","2023-01-15","A comprehensive guide...","https://...","450","English","Tech Press","['John Doe', 'Jane Smith']","['Programming', 'Technology']","/content/book_1",125000
```

#### CSV Format for Authors

```csv
id,last_name,first_name,biography,photo_url,birth_date,nationality
1,"Doe","John","John Doe is a software engineer...","https://...","1980-05-15","American"
```

#### CSV Format for Genres

```csv
id,name,description
1,"Programming","Books about software development and programming languages"
```

### Bulk Data Loading Script

Create `load_institutional_data.py`:

```python
import pandas as pd
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models.book_model import Book
from models.author_model import Author
from models.genre_model import Genre
import json

def load_books(csv_path: str, db: Session):
    """Load books from CSV file"""
    df = pd.read_csv(csv_path)
    
    for _, row in df.iterrows():
        book = Book(
            titre=row['title'],
            isbn=row['isbn'],
            date_publication=pd.to_datetime(row['publication_date']),
            description=row['description'],
            image_url=row['image_url'],
            nombre_pages=row['pages'],
            total_pages=row['pages'],
            langue=row['language'],
            editeur=row['publisher'],
            author_names=json.loads(row['author_names']),
            genre_names=json.loads(row['genre_names']),
            content_path=row['content_path'],
            word_count=row['word_count']
        )
        db.add(book)
    
    db.commit()
    print(f"Loaded {len(df)} books")

def load_authors(csv_path: str, db: Session):
    """Load authors from CSV file"""
    df = pd.read_csv(csv_path)
    
    for _, row in df.iterrows():
        author = Author(
            nom=row['last_name'],
            prenom=row['first_name'],
            biographie=row['biography'],
            photo_url=row['photo_url'],
            date_naissance=pd.to_datetime(row['birth_date']),
            nationalite=row['nationality']
        )
        db.add(author)
    
    db.commit()
    print(f"Loaded {len(df)} authors")

def load_genres(csv_path: str, db: Session):
    """Load genres from CSV file"""
    df = pd.read_csv(csv_path)
    
    for _, row in df.iterrows():
        genre = Genre(
            nom=row['name'],
            description=row['description']
        )
        db.add(genre)
    
    db.commit()
    print(f"Loaded {len(df)} genres")

if __name__ == "__main__":
    db = SessionLocal()
    
    try:
        print("Loading genres...")
        load_genres("/data/institutional_books/genres.csv", db)
        
        print("Loading authors...")
        load_authors("/data/institutional_books/authors.csv", db)
        
        print("Loading books...")
        load_books("/data/institutional_books/books.csv", db)
        
        print("Data loading complete!")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()
```

### Running the Bulk Load

```bash
# Install pandas if not already installed
pip install pandas

# Run the loading script
python load_institutional_data.py
```

### Performance Optimization for Large Datasets

#### Batch Insert Strategy

```python
def load_books_batch(csv_path: str, db: Session, batch_size: int = 1000):
    """Load books in batches for better performance"""
    df = pd.read_csv(csv_path)
    
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        books = []
        
        for _, row in batch.iterrows():
            book = Book(
                titre=row['title'],
                isbn=row['isbn'],
                # ... other fields
            )
            books.append(book)
        
        db.bulk_save_objects(books)
        db.commit()
        print(f"Loaded batch {i//batch_size + 1}: {len(books)} books")
```

### Database Indexes for Performance

The following indexes are automatically created by migrations:

```sql
-- Full-text search indexes
CREATE INDEX idx_books_titre_gin ON books USING gin(to_tsvector('english', titre));

-- Array search indexes
CREATE INDEX idx_books_authors_gin ON books USING gin(author_names);
CREATE INDEX idx_books_genres_gin ON books USING gin(genre_names);

-- Sorting and filtering indexes
CREATE INDEX idx_books_rating ON books(average_rating DESC);
CREATE INDEX idx_books_publication ON books(date_publication);
CREATE INDEX idx_books_isbn ON books(isbn);
```

### Verification Queries

After loading data, verify with these queries:

```sql
-- Count records
SELECT COUNT(*) FROM books;
SELECT COUNT(*) FROM authors;
SELECT COUNT(*) FROM genres;
SELECT COUNT(*) FROM users;

-- Check data integrity
SELECT COUNT(*) FROM books WHERE author_names IS NULL;
SELECT COUNT(*) FROM books WHERE genre_names IS NULL;

-- Performance test
EXPLAIN ANALYZE SELECT * FROM books WHERE 'Programming' = ANY(genre_names);
```

---

## Appendix

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/booklook
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20

# Redis
REDIS_URL=redis://localhost:6379
REDIS_TTL=3600

# Application
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Pagination
DEFAULT_PAGE_SIZE=20
MAX_PAGE_SIZE=100
```

### Project Structure

```
booklook/
├── src/
│   ├── models/              # Domain models
│   ├── repositories/        # Data access layer
│   ├── controllers/         # Business logic
│   ├── routes/              # API endpoints
│   ├── helpers/             # Utilities
│   ├── middleware/          # Middleware
│   ├── schemas/             # Pydantic schemas
│   ├── alembic/             # Database migrations
│   ├── database.py          # DB connection
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── pages/           # Next.js pages
│   │   ├── components/      # React components
│   │   └── services/        # API clients
│   └── package.json
├── docker/
│   └── docker-compose.yml   # Docker services
├── main.py                  # Application entry point
└── README.md
```

---

## Summary

This comprehensive report provides:

1. **System Architecture**: High-level and MVC architecture diagrams
2. **Database Design**: Complete ERD and SQL schema with indexes
3. **Class Diagrams**: Domain models, repositories, and controllers
4. **Use Case Diagrams**: All user interactions and admin functions
5. **Sequence Diagrams**: Key workflows and API interactions
6. **Component Diagrams**: Frontend and backend component structure
7. **Deployment Architecture**: Docker and network diagrams
8. **API Documentation**: Complete endpoint reference
9. **Data Loading Guide**: Scripts and procedures for loading the Institutional Books dataset

The system is designed for:
- **Scalability**: Horizontal scaling with load balancing
- **Performance**: Caching, database replication, and optimized queries
- **Maintainability**: Clean MVC architecture with separation of concerns
- **Reliability**: High availability with master-slave replication

For questions or support, refer to the project documentation or contact the development team.
