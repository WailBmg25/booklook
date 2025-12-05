# Book Cover Image Fix

## Issue
The backend was not sending the `image_url` field to the frontend, causing all books to show generated covers even when they had cover URLs in the database.

## Changes Made

### Backend Schema Update
**File:** `src/schemas/book_schemas.py`

Added `image_url: Optional[str] = None` to both:
- `BookResponse` schema
- `BookDetailResponse` schema

This ensures the cover URL is included in all API responses.

## Database Commands

### Current Running Containers
Based on `docker ps`, your active containers are:
- `booklook_postgres` - PostgreSQL database
- `booklook_redis` - Redis cache
- `booklook_backend` - FastAPI backend
- `booklook_frontend` - Next.js frontend
- `booklook_nginx` - Nginx reverse proxy
- `booklook_pgadmin` - pgAdmin interface

### Database Queries
Container name: `booklook_postgres`

```bash
# Count books with and without covers (CORRECT QUERY)
docker exec -it booklook_postgres psql -U bookuser -d book_library -c "SELECT COUNT(*) as total_books, COUNT(image_url) as books_with_url, COUNT(*) FILTER (WHERE image_url IS NULL OR image_url = '') as books_without_url FROM books;"

# Check books with cover URLs (show first 10)
docker exec -it booklook_postgres psql -U bookuser -d book_library -c "SELECT id, titre, image_url FROM books WHERE image_url IS NOT NULL AND image_url != '' LIMIT 10;"

# Get sample of books without covers
docker exec -it booklook_postgres psql -U bookuser -d book_library -c "SELECT id, titre FROM books WHERE image_url IS NULL OR image_url = '' LIMIT 10;"

# Check specific book by ID
docker exec -it booklook_postgres psql -U bookuser -d book_library -c "SELECT id, titre, image_url, author_names FROM books WHERE id = 1;"
```

### Current Database Status (as of last check)
- **Total books:** 303
- **Books with cover URLs:** 104 (34%)
- **Books without covers:** 199 (66%)

The 199 books without covers will display the generated leather-book style covers.

## Deployment Steps

1. **Commit changes:**
   ```bash
   git add src/schemas/book_schemas.py
   git commit -m "Add image_url field to book API responses"
   git push origin main
   ```

2. **On production server:**
   ```bash
   git pull origin main
   docker-compose -f docker-compose.prod.yml restart backend
   ```

3. **Verify the fix:**
   - Check API response includes image_url: `curl http://localhost:8000/api/books/1`
   - Check frontend displays covers correctly

## Frontend Behavior

The `BookCover` component already handles both cases:
- **With image_url:** Displays the actual cover image
- **Without image_url:** Shows generated cover with:
  - Leather-like texture
  - Book title in serif font
  - Consistent color gradient based on title
  - Book spine effect
  - Decorative elements

## Database Schema

The `books` table has the `image_url` column:
```sql
image_url VARCHAR(500) NULL
```

This field is populated by the institutional dataset loader (`load_institutional_books.ipynb`) which fetches covers from Google Books API.
