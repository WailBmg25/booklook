# Enhanced BookLook Design Document

## Overview

BookLook is a production-ready, high-performance web application designed to handle large book datasets (>300GB) with real-time search, concurrent user access, and smooth text-based reading experiences. The system focuses on simplicity and performance, using Docker for easy deployment and database replication for high availability.

## Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Load Balancer"
        LB[Nginx Load Balancer]
    end

    subgraph "Frontend"
        UI[Next.js + Tailwind]
        AUTH_UI[NextAuth Authentication]
    end

    subgraph "Backend Services"
        API1[FastAPI Instance 1]
        API2[FastAPI Instance 2]
        API3[FastAPI Instance N...]
    end

    subgraph "Caching Layer"
        REDIS_M[Redis Master]
        REDIS_S[Redis Slaves]
    end

    subgraph "Database Cluster"
        PG_M[(PostgreSQL Master)]
        PG_R1[(PostgreSQL Read Replica 1)]
        PG_R2[(PostgreSQL Read Replica 2)]
    end

    subgraph "Search & Storage"
        ES[(Elasticsearch Cluster)]
        FS[File Storage for Book Content]
    end

    LB --> UI
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
    API3 --> ES
    API1 --> FS
```

### Technology Stack

- **Frontend**: Next.js 14 with Tailwind CSS for responsive UI
- **Authentication**: NextAuth.js for simple email/password authentication
- **Backend**: FastAPI with multiple instances for horizontal scaling
- **Database**: PostgreSQL with master-slave replication for high availability
- **Caching**: Redis cluster for session management and query caching
- **Search**: Elasticsearch for real-time book search and filtering
- **Deployment**: Docker Compose for development, Docker Swarm/Kubernetes for production
- **Load Balancing**: Nginx for distributing requests across FastAPI instances

## Components and Interfaces

### 1. Frontend Application (Next.js)

#### Pages Structure

```
/pages
  /auth
    - login.tsx (email, password)
    - register.tsx (email, first_name, last_name, password, confirm_password)
  - index.tsx (books table with filters)
  - book/[id].tsx (book details, reviews, reading interface)
  - read/[id].tsx (full-screen reading mode)
```

#### Key Components

- **BooksTable**: Displays books with pagination, sorting, and filtering
- **BookFilters**: Genre, author, publication year, rating filters
- **BookReader**: Scrolling text reader with progress tracking
- **ReviewSection**: Display and submit reviews
- **AuthForms**: Simple login/register forms with NextAuth

### 2. Backend API (FastAPI)

#### Core Routes

```python
# Authentication
POST /auth/register
POST /auth/login
POST /auth/logout

# Books
GET /books?page=1&size=20&genre=&author=&search=
GET /books/{book_id}
GET /books/{book_id}/content?page=1  # Paginated content for performance
GET /books/{book_id}/reviews

# Reviews
POST /books/{book_id}/reviews
GET /reviews/{review_id}
PUT /reviews/{review_id}
DELETE /reviews/{review_id}

# User
GET /user/profile
PUT /user/profile
GET /user/favorites
POST /user/favorites/{book_id}
DELETE /user/favorites/{book_id}

# Reading Progress
GET /user/reading-progress/{book_id}
PUT /user/reading-progress/{book_id}
```

#### Service Layer

```python
class BookService:
    async def get_books_paginated(self, filters: BookFilters) -> PaginatedBooks
    async def get_book_content(self, book_id: int, page: int) -> BookContent
    async def search_books(self, query: str) -> List[Book]

class ReviewService:
    async def create_review(self, user_id: int, book_id: int, review: ReviewCreate) -> Review
    async def get_book_reviews(self, book_id: int) -> List[Review]

class UserService:
    async def create_user(self, user_data: UserCreate) -> User
    async def authenticate_user(self, email: str, password: str) -> Optional[User]
```

### 3. Database Design

#### Optimized Schema for Large Data

```sql
-- Partitioned books table for >300GB data
CREATE TABLE books (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    isbn VARCHAR(20) UNIQUE,
    author_names TEXT[], -- Denormalized for faster search
    genre_names TEXT[], -- Denormalized for faster filtering
    publication_year INTEGER,
    description TEXT,
    content_path VARCHAR(500), -- Path to content file
    word_count INTEGER,
    average_rating DECIMAL(3,2) DEFAULT 0,
    review_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY RANGE (publication_year);

-- Indexes for performance
CREATE INDEX idx_books_title_gin ON books USING gin(to_tsvector('english', title));
CREATE INDEX idx_books_authors_gin ON books USING gin(author_names);
CREATE INDEX idx_books_genres_gin ON books USING gin(genre_names);
CREATE INDEX idx_books_rating ON books(average_rating DESC);

-- Reading progress for pagination
CREATE TABLE reading_progress (
    user_id INTEGER REFERENCES users(id),
    book_id INTEGER REFERENCES books(id),
    current_page INTEGER DEFAULT 1,
    total_pages INTEGER,
    last_read_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, book_id)
);
```

### 4. Content Storage Strategy

#### Book Content Management

- **Storage**: Files stored in organized directory structure `/content/books/{book_id}/`
- **Format**: Plain text files split into pages (1000-2000 words per page)
- **Caching**: Frequently accessed pages cached in Redis
- **Delivery**: Pagination-based content delivery for performance

#### Content Structure

```
/content
  /books
    /1
      - metadata.json (title, author, total_pages, etc.)
      - page_001.txt
      - page_002.txt
      - ...
    /2
      - metadata.json
      - page_001.txt
      - ...
```

## Data Models

### Simplified User Model

```python
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)
```

### Optimized Book Model

```python
class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False, index=True)
    isbn = Column(String(20), unique=True)
    author_names = Column(ARRAY(String), index=True)  # Denormalized
    genre_names = Column(ARRAY(String), index=True)   # Denormalized
    publication_year = Column(Integer, index=True)
    description = Column(Text)
    content_path = Column(String(500))
    word_count = Column(Integer)
    total_pages = Column(Integer)
    average_rating = Column(Numeric(3, 2), default=0)
    review_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
```

### Review Model

```python
class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    title = Column(String(200))
    content = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
```

## Performance Optimizations

### Database Performance

- **Read Replicas**: Separate read operations to replica databases
- **Connection Pooling**: Optimized pool sizes for concurrent users
- **Query Optimization**: Indexed searches, denormalized data for common queries
- **Partitioning**: Table partitioning for large datasets

### Caching Strategy

- **Redis Layers**:
  - L1: Book metadata (30min TTL)
  - L2: Search results (15min TTL)
  - L3: Book content pages (60min TTL)
- **Application Cache**: In-memory caching for frequently accessed data

### Content Delivery

- **Pagination**: Content delivered in manageable chunks
- **Lazy Loading**: Load content as user scrolls
- **Compression**: Gzip compression for text content
- **CDN**: Static assets served via CDN

## Error Handling

### API Error Responses

```python
class APIError(BaseModel):
    error_code: str
    message: str
    details: Optional[Dict] = None

# Standard error responses
HTTP_400_BAD_REQUEST: "Invalid request parameters"
HTTP_401_UNAUTHORIZED: "Authentication required"
HTTP_404_NOT_FOUND: "Resource not found"
HTTP_429_TOO_MANY_REQUESTS: "Rate limit exceeded"
HTTP_500_INTERNAL_ERROR: "Internal server error"
```

### Graceful Degradation

- Search service unavailable → Basic database search
- Cache unavailable → Direct database queries
- Content service down → Error message with retry option

## Testing Strategy

### Backend Testing

- **Unit Tests**: Service layer logic, data validation
- **Integration Tests**: Database operations, API endpoints
- **Load Tests**: Concurrent user simulation, database performance
- **Performance Tests**: Response time benchmarks, memory usage

### Frontend Testing

- **Component Tests**: React component functionality
- **E2E Tests**: Complete user workflows
- **Performance Tests**: Page load times, rendering performance

## Deployment Architecture

### Docker Configuration

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    ports: ['80:80', '443:443']

  frontend:
    build: ./frontend
    replicas: 2

  backend:
    build: ./backend
    replicas: 3
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres-master:5432/booklook
      - REDIS_URL=redis://redis-master:6379

  postgres-master:
    image: postgres:15
    environment:
      - POSTGRES_REPLICATION_MODE=master

  postgres-replica:
    image: postgres:15
    environment:
      - POSTGRES_REPLICATION_MODE=slave
      - POSTGRES_MASTER_SERVICE=postgres-master

  redis-master:
    image: redis:7-alpine

  elasticsearch:
    image: elasticsearch:8.8.0
    environment:
      - discovery.type=single-node
```

### Scaling Strategy

- **Horizontal Scaling**: Multiple FastAPI instances behind load balancer
- **Database Scaling**: Master-slave replication with read/write splitting
- **Cache Scaling**: Redis cluster for high availability
- **Auto-scaling**: Container orchestration based on CPU/memory usage
