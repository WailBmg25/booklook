# Testing Guide - Institutional Dataset Fixes

This guide walks you through testing all the fixes for the institutional dataset issues.

## Prerequisites

- Backend server running (FastAPI)
- Frontend server running (Next.js)
- PostgreSQL database accessible
- HuggingFace account with access token

## Step 1: Clean the Database

Before loading new data, clean the existing books database:

```bash
# Run the cleanup script
python clean_books_database.py
```

**Expected Output:**
- Shows current counts of books, pages, and authors
- Asks for confirmation
- Deletes all data
- Shows final counts (should all be 0)

## Step 2: Prepare the Notebook

1. **Open the notebook:**
   ```bash
   jupyter notebook load_institutional_books.ipynb
   ```

2. **Update Configuration (Cell 3):**
   - Replace `YOUR_HUGGINGFACE_TOKEN_HERE` with your actual token
   - Verify database configuration matches your setup:
     ```python
     DB_CONFIG = {
         'host': 'localhost',
         'port': 5432,
         'database': 'book_library',
         'user': 'bookuser',
         'password': 'bookpass123'
     }
     ```
   - Adjust `CHUNK_SIZE` and `MAX_CHUNKS` if needed:
     ```python
     CHUNK_SIZE = 50  # Books per batch
     MAX_CHUNKS = 10  # Total batches (None for all)
     ```

## Step 3: Run the Notebook

Execute cells in order:

### Cell 1: Install Dependencies
```bash
!pip install datasets huggingface-hub psycopg2-binary requests pandas -q
```
**Expected:** Packages install successfully

### Cell 2: Import Libraries
**Expected:** "✅ All imports successful!"

### Cell 3: Configuration
**Expected:** Shows dataset name, chunk size, max chunks, words per page

### Cell 4: Helper Functions
**Expected:** 
- "✅ Cover fetching function defined"
- "✅ Description generation function defined"
- "✅ Page splitting function defined"
- "✅ Author parsing function defined"

### Cell 5: Database Connection
**Expected:** 
- "✅ Connected to database"
- "📚 Current books in database: 0"

### Cell 6: Load Progress
**Expected:** "📊 Progress loaded: 0 books processed"

### Cell 7: HuggingFace Login
**Expected:** "✅ Logged in to HuggingFace"

### Cell 8: Load Dataset and Process Books
**Expected Output for Each Book:**
```
============================================================
📖 Processing book 1: [Book Title]
  📝 Description: [First 100 chars]...
  ✓ Using dataset image / ✓ Using Google Books image / ✗ No cover image found
  👤 Created author: [Author Name] / 👤 Found existing author: [Author Name]
  📚 Created book (ID: [ID])
  📄 Creating [N] pages...
  ✅ Added [N] pages
  ✅ Book processed successfully

📊 Progress: [N] books | [X.XX] books/sec
```

**Final Output:**
```
============================================================
✅ Processing complete!
📚 Total books processed: [N]
❌ Errors: [N]
⏱️  Total time: [X.XX] seconds
```

## Step 4: Verify Database Content

Check that data was loaded correctly:

```bash
# Check book count
python -c "
import sys
sys.path.insert(0, 'src')
from database import SessionLocal
from models.book_model import Book
from models.book_page_model import BookPage
from models.author_model import Author

db = SessionLocal()
print(f'Books: {db.query(Book).count()}')
print(f'Pages: {db.query(BookPage).count()}')
print(f'Authors: {db.query(Author).count()}')

# Check a sample book
book = db.query(Book).first()
if book:
    print(f'\nSample Book:')
    print(f'  Title: {book.titre}')
    print(f'  Authors: {book.author_names}')
    print(f'  Description: {book.description[:100]}...')
    print(f'  Total Pages: {book.total_pages}')
    print(f'  Has Content: {book.has_content()}')
db.close()
"
```

**Expected Output:**
- Books: [N] (should match processed count)
- Pages: [N] (should be > 0)
- Authors: [N] (should be > 0)
- Sample book shows:
  - Valid title
  - Author names in array format
  - Description (not empty)
  - Total pages > 0
  - Has content: True

## Step 5: Test Backend API

### Test 1: Get Books List
```bash
curl http://localhost:8000/books | jq '.books[0]'
```

**Expected:**
- Returns list of books
- Each book has `author_names` array
- Each book has `description`
- Each book has `total_pages`

### Test 2: Get Book Details
```bash
# Replace {book_id} with actual ID
curl http://localhost:8000/books/{book_id} | jq '.'
```

**Expected:**
- Returns book details
- `author_names` is populated array
- `description` is not empty
- `total_pages` > 0

### Test 3: Get Book Content
```bash
# Replace {book_id} with actual ID
curl "http://localhost:8000/books/{book_id}/content?page=1" | jq '.'
```

**Expected:**
```json
{
  "book_id": 1,
  "book_title": "Book Title",
  "page": 1,
  "total_pages": 10,
  "content": "Actual book content here...",
  "has_next": true,
  "has_previous": false
}
```

**Important:** Content should be REAL text from the book, NOT generated placeholder text like "The morning sun cast long shadows..."

### Test 4: Navigate Pages
```bash
# Test page 2
curl "http://localhost:8000/books/{book_id}/content?page=2" | jq '.content'
```

**Expected:**
- Different content than page 1
- Real book text
- `has_previous` should be true
- `has_next` depends on total pages

## Step 6: Test Frontend

### Test 1: Books List Page
1. Open browser: `http://localhost:3000`
2. **Check:**
   - Books are displayed
   - Author names show correctly (not "Unknown Author")
   - Descriptions are visible

### Test 2: Book Detail Page
1. Click on any book
2. **Check:**
   - ✅ Author name displays correctly (not "Unknown Author")
   - ✅ Author name shows multiple authors with commas if applicable
   - ✅ Description is visible and meaningful
   - ✅ "Read Book" button is present

### Test 3: Reading Page
1. Click "Read Book" button
2. **Check:**
   - ✅ Book title displays in header
   - ✅ Author name displays correctly (not "Unknown Author")
   - ✅ Content shows REAL book text (not generated placeholder)
   - ✅ Page navigation works (Previous/Next buttons)
   - ✅ Page number shows correctly
   - ✅ Progress percentage updates
   - ✅ Content changes when navigating to different pages

### Test 4: Content Verification
1. Read page 1 content
2. Click "Next" to go to page 2
3. **Verify:**
   - Content is DIFFERENT from page 1
   - Content is REAL book text
   - No repeated "[Page X, Section Y]" markers
   - No generic template text

## Step 7: Test Edge Cases

### Test 1: Book Without Content
If you have a book without pages:
```bash
curl "http://localhost:8000/books/{book_id}/content?page=1"
```

**Expected:**
```json
{
  "error": "NO_CONTENT",
  "message": "This book has no content available yet..."
}
```

### Test 2: Invalid Page Number
```bash
curl "http://localhost:8000/books/{book_id}/content?page=9999"
```

**Expected:** 404 error

### Test 3: Multiple Authors
Find a book with multiple authors and verify:
- Frontend shows: "Author1, Author2, Author3"
- Not just the first author

## Troubleshooting

### Issue: "Unknown Author" still showing
**Solution:** 
- Check API response has `author_names` field
- Clear browser cache
- Restart frontend server

### Issue: Generated content instead of real content
**Solution:**
- Verify BookPage records exist in database
- Check backend logs for errors
- Restart backend server to clear cache

### Issue: Notebook fails to connect to database
**Solution:**
- Verify database is running
- Check DB_CONFIG credentials
- Test connection: `psql -h localhost -U bookuser -d book_library`

### Issue: No cover images
**Solution:**
- This is expected if dataset URLs are invalid
- Google Books API fallback may not find all books
- Books will still load without images

### Issue: Descriptions are "No description available"
**Solution:**
- Check if book has `text` field in dataset
- Verify `generate_description()` function is working
- Some books may genuinely have no text

## Success Criteria

✅ All checks pass:
1. Database has books, pages, and authors
2. API returns books with author_names array
3. API returns real book content (not generated)
4. Frontend shows author names correctly
5. Frontend reading page shows real content
6. Page navigation works and shows different content
7. No "Unknown Author" on books with authors
8. No generated placeholder text in reading view

## Cleanup After Testing

To clean up and start fresh:
```bash
python clean_books_database.py
```

Then re-run the notebook to load fresh data.
