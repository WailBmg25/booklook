# Quick Start Checklist - Testing Fixed Issues

## On Your Server

### 1. Pull Latest Changes
```bash
cd /path/to/booklook
git pull origin main
```

### 2. Clean the Database
```bash
# This will delete ALL books, pages, and authors
python clean_books_database.py
```
**Type "yes" when prompted**

### 3. Restart Backend (to clear cache)
```bash
# Stop current backend
pkill -f uvicorn

# Start backend
cd /path/to/booklook
python main.py
```

### 4. Restart Frontend (to clear cache)
```bash
# Stop current frontend
pkill -f "next"

# Start frontend
cd /path/to/booklook/frontend
npm run dev
```

### 5. Open Jupyter Notebook
```bash
jupyter notebook load_institutional_books.ipynb
```

### 6. Update Notebook Configuration (Cell 3)
Replace:
```python
HF_TOKEN = "YOUR_HUGGINGFACE_TOKEN_HERE"
```
With your actual HuggingFace token.

Verify database config:
```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'book_library',
    'user': 'bookuser',
    'password': 'bookpass123'
}
```

### 7. Run All Notebook Cells
- Click "Cell" → "Run All"
- Or run each cell with Shift+Enter
- Watch for errors in output

**Expected:** 
- ✅ All imports successful
- ✅ Connected to database
- ✅ Logged in to HuggingFace
- 📖 Processing book 1, 2, 3...
- ✅ Processing complete!

### 8. Verify Database Has Data
```bash
python -c "
import sys
sys.path.insert(0, 'src')
from database import SessionLocal
from models.book_model import Book
from models.book_page_model import BookPage

db = SessionLocal()
print(f'Books: {db.query(Book).count()}')
print(f'Pages: {db.query(BookPage).count()}')
db.close()
"
```

**Expected:** Both counts > 0

## Testing in Browser

### 9. Test Books List
Open: `http://your-server:3000`

**Check:**
- [ ] Books are displayed
- [ ] Author names show (not "Unknown Author")
- [ ] Descriptions are visible

### 10. Test Book Detail Page
Click on any book

**Check:**
- [ ] Author name displays correctly
- [ ] Description is visible
- [ ] "Read Book" button works

### 11. Test Reading Page
Click "Read Book"

**Check:**
- [ ] Author name in header (not "Unknown Author")
- [ ] Content shows REAL book text (not template text)
- [ ] Page navigation works (Next/Previous)
- [ ] Content CHANGES when you go to next page
- [ ] No "[Page X, Section Y]" markers
- [ ] No "The morning sun cast long shadows..." template text

### 12. Test API Directly
```bash
# Get first book
curl http://your-server:8000/books | jq '.books[0]'

# Check it has author_names array
curl http://your-server:8000/books | jq '.books[0].author_names'

# Get book content (replace {id} with actual book ID)
curl "http://your-server:8000/books/{id}/content?page=1" | jq '.content'
```

**Check:**
- [ ] author_names is an array with values
- [ ] content is real book text

## Success Criteria

✅ **All Fixed:**
1. Books have real content from database (not generated)
2. Author names display correctly (not "Unknown Author")
3. Descriptions are present
4. Book pages load from database
5. Content is different on each page
6. No template/placeholder text

## If Something Fails

1. **Check backend logs:**
   ```bash
   tail -f /path/to/backend/logs
   ```

2. **Check frontend console:**
   - Open browser DevTools (F12)
   - Look for errors in Console tab

3. **Verify database:**
   ```bash
   psql -h localhost -U bookuser -d book_library
   SELECT COUNT(*) FROM books;
   SELECT COUNT(*) FROM book_pages;
   SELECT COUNT(*) FROM authors;
   ```

4. **Clear all caches:**
   - Restart backend
   - Restart frontend
   - Clear browser cache (Ctrl+Shift+Delete)

5. **Check detailed guide:**
   - See `TESTING_GUIDE.md` for comprehensive troubleshooting

## Quick Verification Commands

```bash
# Check if backend is running
curl http://localhost:8000/books | jq '.books | length'

# Check if frontend is running
curl http://localhost:3000

# Check database connection
psql -h localhost -U bookuser -d book_library -c "SELECT COUNT(*) FROM books;"

# Check book has pages
psql -h localhost -U bookuser -d book_library -c "SELECT b.titre, COUNT(bp.id) as pages FROM books b LEFT JOIN book_pages bp ON b.id = bp.book_id GROUP BY b.id, b.titre LIMIT 5;"
```

## Need Help?

See `TESTING_GUIDE.md` for detailed step-by-step testing instructions with expected outputs and troubleshooting.
