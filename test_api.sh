#!/bin/bash

# BookLook API Test Script
# Run this script after starting the server with: python main.py

BASE_URL="http://localhost:8000/api/v1"
TOKEN=""
BOOK_ID=""
REVIEW_ID=""

echo "=========================================="
echo "BookLook API Testing Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test 1: Register User
echo -e "${BLUE}Test 1: Register User${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234",
    "first_name": "John",
    "last_name": "Doe"
  }')
echo "$REGISTER_RESPONSE" | jq '.'
echo ""

# Test 2: Login User
echo -e "${BLUE}Test 2: Login User${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234"
  }')
echo "$LOGIN_RESPONSE" | jq '.'
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.token')
echo -e "${GREEN}Token: $TOKEN${NC}"
echo ""

# Test 3: Get User Profile
echo -e "${BLUE}Test 3: Get User Profile${NC}"
curl -s -X GET "$BASE_URL/user/profile" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo ""

# Test 4: Get All Books
echo -e "${BLUE}Test 4: Get All Books (First Page)${NC}"
BOOKS_RESPONSE=$(curl -s -X GET "$BASE_URL/books?page=1&page_size=5")
echo "$BOOKS_RESPONSE" | jq '.'
BOOK_ID=$(echo "$BOOKS_RESPONSE" | jq -r '.books[0].id')
echo -e "${GREEN}Using Book ID: $BOOK_ID${NC}"
echo ""

# Test 5: Get Book Details
echo -e "${BLUE}Test 5: Get Book Details${NC}"
curl -s -X GET "$BASE_URL/books/$BOOK_ID" | jq '.'
echo ""

# Test 6: Get Book Content
echo -e "${BLUE}Test 6: Get Book Content (Page 1)${NC}"
curl -s -X GET "$BASE_URL/books/$BOOK_ID/content?page=1&words_per_page=300" | jq '.'
echo ""

# Test 7: Add Book to Favorites
echo -e "${BLUE}Test 7: Add Book to Favorites${NC}"
curl -s -X POST "$BASE_URL/user/favorites/$BOOK_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo ""

# Test 8: Get User Favorites
echo -e "${BLUE}Test 8: Get User Favorites${NC}"
curl -s -X GET "$BASE_URL/user/favorites?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo ""

# Test 9: Create Review
echo -e "${BLUE}Test 9: Create Review${NC}"
REVIEW_RESPONSE=$(curl -s -X POST "$BASE_URL/reviews/books/$BOOK_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 5,
    "title": "Excellent book!",
    "content": "This book was amazing. Highly recommended for anyone interested in the topic."
  }')
echo "$REVIEW_RESPONSE" | jq '.'
REVIEW_ID=$(echo "$REVIEW_RESPONSE" | jq -r '.id')
echo -e "${GREEN}Review ID: $REVIEW_ID${NC}"
echo ""

# Test 10: Get Book Reviews
echo -e "${BLUE}Test 10: Get Book Reviews${NC}"
curl -s -X GET "$BASE_URL/books/$BOOK_ID/reviews?page=1&page_size=10" | jq '.'
echo ""

# Test 11: Update Reading Progress
echo -e "${BLUE}Test 11: Update Reading Progress${NC}"
curl -s -X PUT "$BASE_URL/user/reading-progress/$BOOK_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_page": 50,
    "total_pages": 300
  }' | jq '.'
echo ""

# Test 12: Get Reading Progress
echo -e "${BLUE}Test 12: Get Reading Progress${NC}"
curl -s -X GET "$BASE_URL/user/reading-progress/$BOOK_ID" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo ""

# Test 13: Get Currently Reading
echo -e "${BLUE}Test 13: Get Currently Reading Books${NC}"
curl -s -X GET "$BASE_URL/user/reading-progress-currently-reading?limit=10" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo ""

# Test 14: Update Review
echo -e "${BLUE}Test 14: Update Review${NC}"
curl -s -X PUT "$BASE_URL/reviews/$REVIEW_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "rating": 4,
    "title": "Great book!",
    "content": "Updated review: Still a great book, but I found some minor issues."
  }' | jq '.'
echo ""

# Test 15: Get My Reviews
echo -e "${BLUE}Test 15: Get My Reviews${NC}"
curl -s -X GET "$BASE_URL/reviews/user/my-reviews?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
echo ""

# Test 16: Search Books
echo -e "${BLUE}Test 16: Search Books${NC}"
curl -s -X GET "$BASE_URL/books?search=python&page=1&page_size=5" | jq '.'
echo ""

echo -e "${GREEN}=========================================="
echo "All tests completed!"
echo "==========================================${NC}"
