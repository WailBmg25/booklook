#!/bin/bash

# Manual hook to commit Phase 3 completion
# Run this script to commit all Phase 3 changes

echo "=========================================="
echo "Committing Phase 3 Completion"
echo "=========================================="
echo ""

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"
echo ""

# Stage all changes
echo "Staging all changes..."
git add -A

# Show status
echo ""
echo "Changes to be committed:"
git status --short
echo ""

# Create detailed commit message
COMMIT_MSG="Phase 3 Complete: FastAPI Controllers (API endpoints)

✅ All 26 API endpoints implemented and tested (100% success rate)

Implemented:
- 4 Book endpoints (list, details, content, reviews)
- 3 Authentication endpoints (register, login, logout)
- 3 User profile endpoints (get, update, favorites)
- 3 Favorites endpoints (add, check, remove)
- 6 Review endpoints (CRUD + list operations)
- 6 Reading progress endpoints (track, update, history)
- 1 Error handling validation

Deliverables:
- Pydantic schemas for all request/response models
- FastAPI routes with proper error handling
- Authentication middleware with Bearer tokens
- Pagination and filtering support
- Full-text search implementation
- Comprehensive test suite
- Postman collection
- Complete API documentation

Bugs Fixed:
- Timezone comparison issues in models
- Full-text search SQL errors
- Array overlap operator issues
- Pagination response format
- Cache helper with locals()
- Alembic import errors
- Duplicate schema definitions

Test Results: 26/26 endpoints working (100%)
Status: Production Ready ✅"

# Commit changes
echo "Committing changes..."
git commit -m "$COMMIT_MSG"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Commit successful!"
    echo ""
    
    # Push to remote
    echo "Pushing to remote..."
    git push origin $CURRENT_BRANCH
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Push successful!"
        echo ""
        echo "=========================================="
        echo "Phase 3 committed and pushed successfully!"
        echo "=========================================="
    else
        echo ""
        echo "⚠️  Push failed. You may need to push manually."
        echo "Run: git push origin $CURRENT_BRANCH"
    fi
else
    echo ""
    echo "ℹ️  No changes to commit or commit failed."
fi

echo ""
echo "To create a new branch for Phase 4, run:"
echo "  git checkout -b phase-4-frontend"
echo ""
