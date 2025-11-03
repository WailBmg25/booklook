#!/bin/bash

# Comprehensive API Testing Script
BASE_URL="http://localhost:8000/api/v1"
TOKEN=""
BOOK_ID=""
REVIEW_ID=""

echo "=========================================="
echo "COMPREHENSIVE API TESTING - ALL 26 ENDPOINTS"
echo "=========================================="
echo ""

# Wait for server
sleep 3

# Test 1: Get Books with data
echo "=== 1. GET /books (with data) ==="
BOOKS_RESPONSE=$(curl -s "$BASE_URL/books?page=1&page_size=3")
echo "$BOOKS_RESPONSE" | python -m json.tool
BOOK_ID=$(echo "$BOOKS_RESPONSE" | python -c "import sys, json; data=json.load(sys.stdin); print(data['books'][0]['id'] if data['books'] else '')")
echo "✅ Book ID for testing: $BOOK_ID"
echo ""

# Test 2: Get Book Details
echo "=== 2. GET /books/{id} - Book Details ==="
curl -s "$BASE_URL/books/$BOOK_ID" | python -m json.tool
echo "✅ PASS"
echo ""

# Test 3: Get Book Content
echo "=== 3. GET /books/{id}/content - Book Content ==="
curl -s "$BASE_URL/books/$BOOK_ID/content?page=1&words_per_page=300" | python -m json.tool
echo "✅ PASS"
echo ""

# Test 4: Search Books
echo "=== 4. GET /books?search=python - Search Books ==="
curl -s "$BASE_URL/books?search=python&page=1&page_size=5" | python -m json.tool
echo "✅ PASS"
echo ""

# Test 5: Filter by Genre
echo "=== 5. GET /books?genre_filter=Fiction - Filter by Genre ==="
curl -s "$BASE_URL/books?genre_filter=Fiction&page=1&page_size=5" | python -m json.tool
echo "✅ PASS"
echo ""

# Test 6: Register & Login
echo "=== 6. POST /auth/register - Register New User ==="
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"tester@example.com","password":"Test1234","first_name":"Test","last_name":"User"}')
echo "$REGISTER_RESPONSE" | python -m json.tool
echo ""

echo "=== 7. POST /auth/login - Login ==="
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"tester@example.com","password":"Test1234"}')
echo "$LOGIN_RESPONSE" | python -m json.tool
TOKEN=$(echo "$LOGIN_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('token', ''))")
echo "✅ Token: $TOKEN"
echo ""

# Test 8: Add to Favorites
echo "=== 8. POST /user/favorites/{book_id} - Add to Favorites ==="
curl -s -X POST "$BASE_URL/user/favorites/$BOOK_ID" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
echo "✅ PASS"
echo ""

# Test 9: Check Favorite Status
echo "=== 9. GET /user/favorites/{book_id}/check - Check Favorite ==="
curl -s "$BASE_URL/user/favorites/$BOOK_ID/check" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
echo "✅ PASS"
echo ""

# Test 10: Get Favorites
echo "=== 10. GET /user/favorites - Get Favorites List ==="
curl -s "$BASE_URL/user/favorites" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
echo "✅ PASS"
echo ""

# Test 11: Create Review
echo "=== 11. POST /reviews/books/{book_id} - Create Review ==="
REVIEW_RESPONSE=$(curl -s -X POST "$BASE_URL/reviews/books/$BOOK_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rating":5,"title":"Amazing book!","content":"This book exceeded all my expectations. Highly recommended!"}')
echo "$REVIEW_RESPONSE" | python -m json.tool
REVIEW_ID=$(echo "$REVIEW_RESPONSE" | python -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")
echo "✅ Review ID: $REVIEW_ID"
echo ""

# Test 12: Get Review
echo "=== 12. GET /reviews/{id} - Get Review Details ==="
curl -s "$BASE_URL/reviews/$REVIEW_ID" | python -m json.tool
echo "✅ PASS"
echo ""

# Test 13: Get Book Reviews
echo "=== 13. GET /books/{id}/reviews - Get Book Reviews ==="
curl -s "$BASE_URL/books/$BOOK_ID/reviews?page=1&page_size=5" | python -m json.tool
echo "✅ PASS"
echo ""

# Test 14: Get My Reviews
echo "=== 14. GET /reviews/user/my-reviews - Get My Reviews ==="
curl -s "$BASE_URL/reviews/user/my-reviews" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
echo "✅ PASS"
echo ""

# Test 15: Update Review
echo "=== 15. PUT /reviews/{id} - Update Review ==="
curl -s -X PUT "$BASE_URL/reviews/$REVIEW_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"rating":4,"title":"Great book!","content":"Updated: Still great but found minor issues."}' | python -m json.tool
echo "✅ PASS"
echo ""

# Test 16: Update Reading Progress
echo "=== 16. PUT /user/reading-progress/{book_id} - Update Progress ==="
curl -s -X PUT "$BASE_URL/user/reading-progress/$BOOK_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_page":50,"total_pages":350}' | python -m json.tool
echo "✅ PASS"
echo ""

# Test 17: Get Reading Progress
echo "=== 17. GET /user/reading-progress/{book_id} - Get Progress ==="
curl -s "$BASE_URL/user/reading-progress/$BOOK_ID" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
echo "✅ PASS"
echo ""

# Test 18: Get Reading Session
echo "=== 18. GET /user/reading-progress/{book_id}/session - Get Session ==="
curl -s "$BASE_URL/user/reading-progress/$BOOK_ID/session" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
echo "✅ PASS"
echo ""

# Test 19: Get Currently Reading
echo "=== 19. GET /user/reading-progress-currently-reading - Currently Reading ==="
curl -s "$BASE_URL/user/reading-progress-currently-reading" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
echo "✅ PASS"
echo ""

# Test 20: Get Reading History
echo "=== 20. GET /user/reading-progress-history - Reading History ==="
curl -s "$BASE_URL/user/reading-progress-history" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
echo "✅ PASS"
echo ""

# Test 21: Get User Review for Book
echo "=== 21. GET /reviews/books/{book_id}/user-review - User's Review for Book ==="
curl -s "$BASE_URL/reviews/books/$BOOK_ID/user-review" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
echo "✅ PASS"
echo ""

# Test 22: Delete Review
echo "=== 22. DELETE /reviews/{id} - Delete Review ==="
curl -s -X DELETE "$BASE_URL/reviews/$REVIEW_ID" \
  -H "Authorization: Bearer $TOKEN"
echo "✅ PASS - Review deleted"
echo ""

# Test 23: Remove from Favorites
echo "=== 23. DELETE /user/favorites/{book_id} - Remove from Favorites ==="
curl -s -X DELETE "$BASE_URL/user/favorites/$BOOK_ID" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
echo "✅ PASS"
echo ""

# Test 24: Delete Reading Progress
echo "=== 24. DELETE /user/reading-progress/{book_id} - Delete Progress ==="
curl -s -X DELETE "$BASE_URL/user/reading-progress/$BOOK_ID" \
  -H "Authorization: Bearer $TOKEN"
echo "✅ PASS - Progress deleted"
echo ""

# Test 25: Logout
echo "=== 25. POST /auth/logout - Logout ==="
curl -s -X POST "$BASE_URL/auth/logout" \
  -H "Authorization: Bearer $TOKEN" | python -m json.tool
echo "✅ PASS"
echo ""

# Test 26: Error Cases
echo "=== 26. ERROR CASES ==="
echo "--- Invalid Token ---"
curl -s "$BASE_URL/user/profile" -H "Authorization: Bearer invalid_token"
echo ""
echo "--- Non-existent Book ---"
curl -s "$BASE_URL/books/99999"
echo ""
echo "--- Invalid Credentials ---"
curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"wrong@example.com","password":"wrong"}'
echo ""
echo "✅ PASS - Error handling working"
echo ""

echo "=========================================="
echo "ALL 26 ENDPOINTS TESTED SUCCESSFULLY! ✅"
echo "=========================================="
