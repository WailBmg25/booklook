# CSV Import Templates for BookLook Admin

## 📋 Ready-to-Use CSV Templates

### 1. Users Import Template

**Filename**: `users_import_template.csv`

```csv
Email,First Name,Last Name,Password,Is Active,Is Admin
john.doe@example.com,John,Doe,password123,true,false
jane.smith@example.com,Jane,Smith,securepass456,true,false
admin@booklook.com,Admin,User,adminpass789,true,true
alice.johnson@example.com,Alice,Johnson,pass123,true,false
bob.williams@example.com,Bob,Williams,pass456,false,false
```

**Field Descriptions:**
- `Email`: User's email address (required, must be unique)
- `First Name`: User's first name (required)
- `Last Name`: User's last name (required)
- `Password`: Plain text password (will be hashed, default: password123)
- `Is Active`: true/false (default: true)
- `Is Admin`: true/false (default: false)

---

### 2. Books Import Template

**Filename**: `books_import_template.csv`

```csv
Title,ISBN,Authors,Genres,Publication Date,Pages,Language,Publisher,Description
"Python Programming Guide","978-0-123456-78-9","John Doe; Jane Smith","Programming; Technology","2023-01-15",450,English,"Tech Press","A comprehensive guide to Python programming for beginners and experts"
"Data Science Handbook","978-0-234567-89-0","Alice Johnson","Science; Technology; Data","2023-03-20",520,English,"Data Press","Complete guide to data science with practical examples"
"Web Development Mastery","978-0-345678-90-1","Bob Williams; Carol Davis","Programming; Web","2023-06-10",380,English,"Web Publishers","Master modern web development with this comprehensive guide"
"Machine Learning Basics","978-0-456789-01-2","David Brown","Technology; AI; Science","2023-09-05",600,English,"AI Press","Introduction to machine learning concepts and applications"
"Database Design","978-0-567890-12-3","Emma Wilson","Programming; Database","2023-11-20",420,English,"DB Publishers","Learn database design principles and best practices"
```

**Field Descriptions:**
- `Title`: Book title (required)
- `ISBN`: ISBN number (required, must be unique)
- `Authors`: Semicolon-separated list of authors (e.g., "Author1; Author2")
- `Genres`: Semicolon-separated list of genres (e.g., "Genre1; Genre2")
- `Publication Date`: ISO format date (YYYY-MM-DD)
- `Pages`: Number of pages (integer)
- `Language`: Book language (default: English)
- `Publisher`: Publisher name
- `Description`: Book description (use quotes if contains commas)

---

### 3. Reviews Import Template

**Filename**: `reviews_import_template.csv`

```csv
User Email,Book ISBN,Rating,Title,Content
john.doe@example.com,978-0-123456-78-9,5,"Excellent Book","This book was absolutely fantastic! I learned so much about Python programming. The examples are clear and the explanations are thorough. Highly recommended for anyone wanting to learn Python."
jane.smith@example.com,978-0-234567-89-0,4,"Very Good Resource","Great content and well-organized. The data science concepts are explained clearly. Would have given 5 stars if it had more advanced topics."
alice.johnson@example.com,978-0-345678-90-1,5,"Best Web Dev Book","This is hands down the best web development book I've read. Covers everything from basics to advanced topics. The code examples are practical and easy to follow."
bob.williams@example.com,978-0-456789-01-2,3,"Good but Dense","The content is good but quite dense. Takes time to digest. Good for serious learners but might be overwhelming for beginners."
john.doe@example.com,978-0-567890-12-3,4,"Solid Database Guide","Comprehensive coverage of database design. The examples are relevant and the explanations are clear. A must-read for database developers."
```

**Field Descriptions:**
- `User Email`: Email of the user writing the review (must exist in database)
- `Book ISBN`: ISBN of the book being reviewed (must exist in database)
- `Rating`: Rating from 1 to 5 (required)
- `Title`: Review title (optional)
- `Content`: Review content (use quotes if contains commas)

---

## 🎯 Import Guidelines

### General Rules

1. **File Format**: Must be CSV (Comma-Separated Values)
2. **Encoding**: UTF-8 recommended
3. **Headers**: First row must contain column headers (case-sensitive)
4. **Quotes**: Use double quotes for fields containing commas or special characters
5. **Empty Fields**: Leave empty or use empty quotes ""
6. **Boolean Values**: Use "true" or "false" (lowercase)
7. **Dates**: Use ISO format YYYY-MM-DD

### Best Practices

1. **Test with Small Files First**: Import 5-10 records to test format
2. **Check for Duplicates**: Ensure unique values for email/ISBN
3. **Validate Data**: Check all required fields are present
4. **Use Quotes**: Always quote text fields with commas or semicolons
5. **Backup First**: Export existing data before importing new data

---

## 📊 Sample Data Sets

### Small Test Set (5 records each)

**users_test.csv**
```csv
Email,First Name,Last Name,Password,Is Active,Is Admin
test1@example.com,Test,User1,pass123,true,false
test2@example.com,Test,User2,pass123,true,false
test3@example.com,Test,User3,pass123,true,false
test4@example.com,Test,User4,pass123,false,false
test5@example.com,Test,Admin,pass123,true,true
```

**books_test.csv**
```csv
Title,ISBN,Authors,Genres,Publication Date,Pages,Language,Publisher,Description
"Test Book 1","978-0-111111-11-1","Author One","Fiction","2023-01-01",200,English,"Test Press","Test description 1"
"Test Book 2","978-0-222222-22-2","Author Two","Science","2023-02-01",250,English,"Test Press","Test description 2"
"Test Book 3","978-0-333333-33-3","Author Three","History","2023-03-01",300,English,"Test Press","Test description 3"
"Test Book 4","978-0-444444-44-4","Author Four","Technology","2023-04-01",350,English,"Test Press","Test description 4"
"Test Book 5","978-0-555555-55-5","Author Five","Biography","2023-05-01",400,English,"Test Press","Test description 5"
```

**reviews_test.csv**
```csv
User Email,Book ISBN,Rating,Title,Content
test1@example.com,978-0-111111-11-1,5,"Great","Excellent book"
test2@example.com,978-0-222222-22-2,4,"Good","Very informative"
test3@example.com,978-0-333333-33-3,3,"Okay","Average read"
test4@example.com,978-0-444444-44-4,4,"Nice","Well written"
test5@example.com,978-0-555555-55-5,5,"Amazing","Highly recommended"
```

---

## 🔧 Troubleshooting

### Common Errors and Solutions

#### Error: "Invalid CSV format"
**Solution**: Ensure file has .csv extension and proper CSV structure

#### Error: "User with email X already exists"
**Solution**: Remove duplicate emails or use different emails

#### Error: "Book with ISBN X already exists"
**Solution**: Remove duplicate ISBNs or use different ISBNs

#### Error: "User with email X not found" (Reviews)
**Solution**: Import users first, then reviews

#### Error: "Book with ISBN X not found" (Reviews)
**Solution**: Import books first, then reviews

#### Error: "Invalid date format"
**Solution**: Use YYYY-MM-DD format (e.g., 2023-01-15)

#### Error: "Rating must be between 1 and 5"
**Solution**: Ensure rating values are 1, 2, 3, 4, or 5

---

## 📝 Creating Your Own CSV Files

### Using Excel/Google Sheets

1. Create a new spreadsheet
2. Add column headers in first row
3. Fill in data rows
4. File → Save As → CSV (Comma delimited)
5. Ensure UTF-8 encoding

### Using Text Editor

1. Create new file with .csv extension
2. Add headers: `Column1,Column2,Column3`
3. Add data rows: `value1,value2,value3`
4. Use quotes for text with commas: `"value with, comma"`
5. Save with UTF-8 encoding

### Using Python

```python
import csv

# Create users CSV
with open('users.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Email', 'First Name', 'Last Name', 'Password', 'Is Active', 'Is Admin'])
    writer.writerow(['user@example.com', 'John', 'Doe', 'pass123', 'true', 'false'])

# Create books CSV
with open('books.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Title', 'ISBN', 'Authors', 'Genres', 'Publication Date', 'Pages', 'Language', 'Publisher', 'Description'])
    writer.writerow(['Book Title', '978-0-123456-78-9', 'Author Name', 'Genre', '2023-01-15', '300', 'English', 'Publisher', 'Description'])
```

---

## 🎓 Advanced Tips

### Bulk Import Strategy

1. **Order Matters**: Import in this order:
   - Users first
   - Books second
   - Reviews last (requires users and books)

2. **Batch Size**: For large datasets:
   - Split into files of 100-500 records
   - Import one batch at a time
   - Verify each batch before continuing

3. **Error Handling**:
   - Review error messages after each import
   - Fix errors in source file
   - Re-import failed records

### Data Validation

Before importing, validate:
- ✅ All required fields present
- ✅ Email format valid
- ✅ ISBN format valid (13 digits with hyphens)
- ✅ Dates in correct format
- ✅ Ratings between 1-5
- ✅ Boolean values are "true" or "false"

---

## 📦 Download Templates

Save these templates to your computer:

1. **users_import_template.csv** - For importing users
2. **books_import_template.csv** - For importing books
3. **reviews_import_template.csv** - For importing reviews

Modify the templates with your data and import via the admin dashboard!

---

*Templates Version: 1.0*
*Last Updated: November 10, 2025*
*Compatible with: BookLook Admin Dashboard*
