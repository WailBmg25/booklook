"""Book service for handling book-related business logic."""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text, desc, asc
from models.book import Book, Author, Genre, Review
from helpers.config import settings
import redis
import json
import hashlib


class BookService:
    """Service for book-related operations with caching and optimization."""
    
    def __init__(self, db: Session, redis_client: Optional[redis.Redis] = None):
        self.db = db
        self.redis_client = redis_client
        self.cache_ttl = settings.CACHE_TTL
    
    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """Generate cache key from parameters."""
        key_data = f"{prefix}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from Redis cache."""
        if not self.redis_client:
            return None
        try:
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
        except Exception:
            pass
        return None
    
    def _set_cache(self, cache_key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Set data in Redis cache."""
        if not self.redis_client:
            return
        try:
            ttl = ttl or self.cache_ttl
            self.redis_client.setex(cache_key, ttl, json.dumps(data, default=str))
        except Exception:
            pass
    
    def get_books_paginated(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        genre_filter: Optional[List[str]] = None,
        author_filter: Optional[List[str]] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        min_rating: Optional[float] = None,
        sort_by: str = "titre",
        sort_order: str = "asc"
    ) -> Tuple[List[Dict], int, int]:
        """
        Get paginated list of books with filtering and search.
        
        Returns:
            Tuple of (books_list, total_count, total_pages)
        """
        # Create cache key
        cache_key = self._get_cache_key(
            "books_paginated",
            page=page,
            page_size=page_size,
            search=search,
            genre_filter=genre_filter,
            author_filter=author_filter,
            year_from=year_from,
            year_to=year_to,
            min_rating=min_rating,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Try to get from cache
        cached_result = self._get_from_cache(cache_key)
        if cached_result:
            return cached_result["books"], cached_result["total_count"], cached_result["total_pages"]
        
        # Build query
        query = self.db.query(Book)
        
        # Apply search filter using full-text search
        if search:
            search_vector = func.to_tsvector('english', Book.titre + ' ' + func.coalesce(Book.description, ''))
            search_query = func.plainto_tsquery('english', search)
            query = query.filter(search_vector.match(search_query))
        
        # Apply genre filter using array operations
        if genre_filter:
            query = query.filter(Book.genre_names.overlap(genre_filter))
        
        # Apply author filter using array operations
        if author_filter:
            query = query.filter(Book.author_names.overlap(author_filter))
        
        # Apply year filters
        if year_from:
            query = query.filter(func.extract('year', Book.date_publication) >= year_from)
        if year_to:
            query = query.filter(func.extract('year', Book.date_publication) <= year_to)
        
        # Apply rating filter
        if min_rating:
            query = query.filter(Book.average_rating >= min_rating)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply sorting
        sort_column = getattr(Book, sort_by, Book.titre)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))
        
        # Apply pagination
        offset = (page - 1) * page_size
        books = query.offset(offset).limit(page_size).all()
        
        # Convert to dict format
        books_list = []
        for book in books:
            book_dict = {
                "id": book.id,
                "titre": book.titre,
                "isbn": book.isbn,
                "date_publication": book.date_publication,
                "description": book.description,
                "image_url": book.image_url,
                "nombre_pages": book.nombre_pages,
                "total_pages": book.total_pages,
                "langue": book.langue,
                "editeur": book.editeur,
                "average_rating": float(book.average_rating) if book.average_rating else 0.0,
                "review_count": book.review_count or 0,
                "author_names": book.author_names or [],
                "genre_names": book.genre_names or [],
                "word_count": book.word_count,
                "content_path": book.content_path,
                "created_at": book.created_at,
                "updated_at": book.updated_at
            }
            books_list.append(book_dict)
        
        # Calculate total pages
        total_pages = (total_count + page_size - 1) // page_size
        
        # Cache the result
        cache_data = {
            "books": books_list,
            "total_count": total_count,
            "total_pages": total_pages
        }
        self._set_cache(cache_key, cache_data)
        
        return books_list, total_count, total_pages
    
    def get_book_by_id(self, book_id: int) -> Optional[Dict]:
        """Get detailed book information by ID with caching."""
        cache_key = self._get_cache_key("book_detail", book_id=book_id)
        
        # Try cache first
        cached_book = self._get_from_cache(cache_key)
        if cached_book:
            return cached_book
        
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if not book:
            return None
        
        # Get related authors and genres
        authors = self.db.query(Author).join(Book.auteurs).filter(Book.id == book_id).all()
        genres = self.db.query(Genre).join(Book.genres).filter(Book.id == book_id).all()
        
        book_dict = {
            "id": book.id,
            "titre": book.titre,
            "isbn": book.isbn,
            "date_publication": book.date_publication,
            "description": book.description,
            "image_url": book.image_url,
            "nombre_pages": book.nombre_pages,
            "total_pages": book.total_pages,
            "langue": book.langue,
            "editeur": book.editeur,
            "average_rating": float(book.average_rating) if book.average_rating else 0.0,
            "review_count": book.review_count or 0,
            "author_names": book.author_names or [],
            "genre_names": book.genre_names or [],
            "word_count": book.word_count,
            "content_path": book.content_path,
            "created_at": book.created_at,
            "updated_at": book.updated_at,
            "authors": [
                {
                    "id": author.id,
                    "nom": author.nom,
                    "prenom": author.prenom,
                    "biographie": author.biographie,
                    "photo_url": author.photo_url,
                    "date_naissance": author.date_naissance,
                    "nationalite": author.nationalite
                }
                for author in authors
            ],
            "genres": [
                {
                    "id": genre.id,
                    "nom": genre.nom,
                    "description": genre.description
                }
                for genre in genres
            ]
        }
        
        # Cache the result
        self._set_cache(cache_key, book_dict)
        
        return book_dict
    
    def search_books_fulltext(self, query: str, limit: int = 10) -> List[Dict]:
        """Perform full-text search on books with ranking."""
        cache_key = self._get_cache_key("search_books", query=query, limit=limit)
        
        # Try cache first
        cached_results = self._get_from_cache(cache_key)
        if cached_results:
            return cached_results
        
        # Use PostgreSQL full-text search with ranking
        search_query = text("""
            SELECT b.*, 
                   ts_rank(to_tsvector('english', b.titre || ' ' || COALESCE(b.description, '')), 
                          plainto_tsquery('english', :query)) as rank
            FROM books b
            WHERE to_tsvector('english', b.titre || ' ' || COALESCE(b.description, '')) 
                  @@ plainto_tsquery('english', :query)
            ORDER BY rank DESC, b.average_rating DESC
            LIMIT :limit
        """)
        
        result = self.db.execute(search_query, {"query": query, "limit": limit})
        books = result.fetchall()
        
        books_list = []
        for book in books:
            book_dict = {
                "id": book.id,
                "titre": book.titre,
                "isbn": book.isbn,
                "date_publication": book.date_publication,
                "description": book.description,
                "image_url": book.image_url,
                "average_rating": float(book.average_rating) if book.average_rating else 0.0,
                "review_count": book.review_count or 0,
                "author_names": book.author_names or [],
                "genre_names": book.genre_names or [],
                "rank": float(book.rank)
            }
            books_list.append(book_dict)
        
        # Cache results for shorter time (search results change more frequently)
        self._set_cache(cache_key, books_list, ttl=300)  # 5 minutes
        
        return books_list
    
    def get_book_content(self, book_id: int, page: int = 1, words_per_page: int = 300) -> Optional[Dict]:
        """Get paginated book content for reading."""
        cache_key = self._get_cache_key("book_content", book_id=book_id, page=page, words_per_page=words_per_page)
        
        # Try cache first
        cached_content = self._get_from_cache(cache_key)
        if cached_content:
            return cached_content
        
        book = self.db.query(Book).filter(Book.id == book_id).first()
        if not book or not book.content_path:
            return None
        
        # In a real implementation, you would read from the content file
        # For now, we'll simulate content pagination
        total_words = book.word_count or 50000  # Default if not set
        total_pages = (total_words + words_per_page - 1) // words_per_page
        
        if page > total_pages:
            return None
        
        # Simulate content (in real implementation, read from file)
        start_word = (page - 1) * words_per_page
        end_word = min(start_word + words_per_page, total_words)
        
        content_dict = {
            "book_id": book_id,
            "page": page,
            "total_pages": total_pages,
            "words_per_page": words_per_page,
            "start_word": start_word,
            "end_word": end_word,
            "content": f"[Simulated content for book {book.titre}, page {page}. Words {start_word}-{end_word} of {total_words}]",
            "has_next": page < total_pages,
            "has_previous": page > 1
        }
        
        # Cache content for longer time
        self._set_cache(cache_key, content_dict, ttl=3600)  # 1 hour
        
        return content_dict
    
    def get_popular_books(self, limit: int = 10) -> List[Dict]:
        """Get most popular books based on rating and review count."""
        cache_key = self._get_cache_key("popular_books", limit=limit)
        
        cached_books = self._get_from_cache(cache_key)
        if cached_books:
            return cached_books
        
        # Get books ordered by a combination of rating and review count
        books = (
            self.db.query(Book)
            .filter(Book.review_count > 0)
            .order_by(
                desc(Book.average_rating * func.log(Book.review_count + 1))
            )
            .limit(limit)
            .all()
        )
        
        books_list = []
        for book in books:
            book_dict = {
                "id": book.id,
                "titre": book.titre,
                "isbn": book.isbn,
                "image_url": book.image_url,
                "average_rating": float(book.average_rating) if book.average_rating else 0.0,
                "review_count": book.review_count or 0,
                "author_names": book.author_names or [],
                "genre_names": book.genre_names or []
            }
            books_list.append(book_dict)
        
        # Cache for longer time as popular books don't change frequently
        self._set_cache(cache_key, books_list, ttl=1800)  # 30 minutes
        
        return books_list
    
    def invalidate_book_cache(self, book_id: int) -> None:
        """Invalidate cache entries for a specific book."""
        if not self.redis_client:
            return
        
        try:
            # Get all keys that might contain this book
            pattern = f"*book*{book_id}*"
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            
            # Also invalidate general listing caches
            listing_keys = self.redis_client.keys("*books_paginated*")
            if listing_keys:
                self.redis_client.delete(*listing_keys)
                
            popular_keys = self.redis_client.keys("*popular_books*")
            if popular_keys:
                self.redis_client.delete(*popular_keys)
        except Exception:
            pass