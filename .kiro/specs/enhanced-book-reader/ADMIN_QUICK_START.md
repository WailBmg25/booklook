# Admin Interface - Quick Start Guide

## 🚀 Quick Access

### Step 1: Login as Admin
1. Go to: `http://localhost:3000/auth/login`
2. Use credentials:
   - **Email:** `final_test@example.com`
   - **Password:** `Test1234`

### Step 2: Access Admin Dashboard
- After login, navigate to: `http://localhost:3000/admin`
- Or click "Admin Dashboard" in the navigation (visible only to admins)

---

## 📊 Admin Dashboard Features

### 1. Overview Dashboard (`/admin`)
**What you'll see:**
- 📚 Total Books: 5
- 👥 Total Users: 4 (1 admin, 3 regular)
- ⭐ Total Reviews: 4
- 📖 Active Readers: 2
- 📈 Recent activity (last 7 days)
- 🏆 Most reviewed books
- 📊 Rating distribution chart

**Actions:**
- View real-time statistics
- Monitor platform activity
- Identify popular books

---

### 2. User Management (`/admin/users`)
**What you'll see:**
- Complete user list with pagination
- User details: name, email, status, role
- User statistics: reviews, favorites, reading progress

**Actions:**
- 🔍 **Search** users by name or email
- 🟢 **Activate** suspended users
- 🔴 **Suspend** user accounts
- 🗑️ **Delete** users permanently
- 👑 **Promote** users to admin
- 👤 **Revoke** admin privileges
- 🔑 **Reset** user passwords

**Filters:**
- All Users
- Active Users
- Suspended Users

---

### 3. Book Management (`/admin/books`)
**What you'll see:**
- Complete book catalog with pagination
- Book details: title, authors, genres, rating, reviews
- ISBN information

**Actions:**
- 🔍 **Search** books by title or author
- 👁️ **View** book details
- 🗑️ **Delete** books
- ➕ **Add** new books (via API)
- ✏️ **Edit** book information (via API)

---

### 4. Review Moderation (`/admin/reviews`)
**What you'll see:**
- All reviews with full details
- Review sentiment (positive/negative/neutral)
- Flagged reviews queue
- User and book information for each review

**Actions:**
- 🚩 **Flag** reviews for moderation
- ✅ **Approve** flagged reviews
- 🗑️ **Delete** inappropriate reviews
- 🔄 **Toggle** between all reviews and flagged only

**Review Details:**
- Rating (1-5 stars)
- Title and content
- Word count
- Sentiment analysis
- User who wrote it
- Book being reviewed
- Date created

---

## 🔐 Security Features

### Access Control
- ✅ Only users with `is_admin=true` can access
- ✅ Non-admin users are redirected to home
- ✅ All actions require authentication

### Self-Protection
- ❌ Cannot suspend your own account
- ❌ Cannot delete your own account
- ❌ Cannot revoke your own admin role

### Session Management
- Sessions invalidated on user suspension
- Sessions invalidated on user deletion
- Token-based authentication

---

## 🛠️ Admin API Endpoints

### Analytics
```bash
GET /api/v1/admin/analytics/overview
GET /api/v1/admin/analytics/users
GET /api/v1/admin/analytics/books
GET /api/v1/admin/analytics/reviews
```

### User Management
```bash
GET    /api/v1/admin/users
GET    /api/v1/admin/users/{id}
PUT    /api/v1/admin/users/{id}/suspend
PUT    /api/v1/admin/users/{id}/activate
DELETE /api/v1/admin/users/{id}
PUT    /api/v1/admin/users/{id}/promote
PUT    /api/v1/admin/users/{id}/revoke-admin
POST   /api/v1/admin/users/{id}/reset-password
```

### Book Management
```bash
POST   /api/v1/admin/books
PUT    /api/v1/admin/books/{id}
DELETE /api/v1/admin/books/{id}
GET    /api/v1/admin/books/pending
POST   /api/v1/admin/books/bulk-update
```

### Review Moderation
```bash
GET    /api/v1/admin/reviews
GET    /api/v1/admin/reviews/flagged
PUT    /api/v1/admin/reviews/{id}/flag
PUT    /api/v1/admin/reviews/{id}/approve
DELETE /api/v1/admin/reviews/{id}
POST   /api/v1/admin/reviews/bulk-delete
POST   /api/v1/admin/reviews/bulk-flag
POST   /api/v1/admin/reviews/bulk-approve
```

---

## 📝 Common Admin Tasks

### Promote a User to Admin
1. Go to `/admin/users`
2. Find the user
3. Click "Make Admin"
4. Confirm action

### Moderate a Review
1. Go to `/admin/reviews`
2. Click "Flagged Reviews" to see moderation queue
3. Review the content
4. Click "Approve" or "Delete"

### Suspend a User
1. Go to `/admin/users`
2. Find the user
3. Click "Suspend"
4. Confirm action
5. User's sessions are automatically invalidated

### View Platform Statistics
1. Go to `/admin` (dashboard)
2. View overview cards
3. Check recent activity
4. Review popular books
5. Analyze rating distribution

---

## 🔧 Creating Additional Admins

### Via Database
```sql
UPDATE users SET is_admin = true WHERE email = 'user@example.com';
```

### Via Admin Interface
1. Login as existing admin
2. Go to `/admin/users`
3. Find the user
4. Click "Make Admin"

---

## 📊 Current System Stats

Based on test data:
- **Books:** 5 total
- **Users:** 4 total (1 admin, 3 regular)
- **Reviews:** 4 total
- **Active Readers:** 2
- **Average Book Rating:** 1.93/5
- **Average Review Rating:** 4.75/5

---

## 🎯 Tips for Admins

1. **Regular Monitoring**
   - Check flagged reviews daily
   - Monitor user activity weekly
   - Review analytics monthly

2. **User Management**
   - Suspend users for violations, don't delete immediately
   - Keep audit trail of admin actions
   - Communicate with users before major actions

3. **Content Moderation**
   - Flag suspicious reviews for review
   - Delete only clearly inappropriate content
   - Approve legitimate flagged reviews quickly

4. **Platform Health**
   - Monitor active reader count
   - Track review submission trends
   - Identify popular books for promotion

---

## 🆘 Troubleshooting

### Can't Access Admin Dashboard
- ✅ Verify you're logged in
- ✅ Check if your account has `is_admin=true`
- ✅ Clear browser cache and cookies
- ✅ Try logging out and back in

### API Returns 403 Forbidden
- ✅ Verify your token is valid
- ✅ Check if you have admin privileges
- ✅ Ensure token is in Authorization header

### Changes Not Reflecting
- ✅ Refresh the page
- ✅ Check backend logs for errors
- ✅ Verify database connection

---

## 📚 Additional Resources

- **API Documentation:** `http://127.0.0.1:8000/docs`
- **Phase 5 Complete Report:** `.kiro/specs/enhanced-book-reader/PHASE_5_COMPLETE.md`
- **Test Report:** `.kiro/specs/enhanced-book-reader/PHASE_5_TEST_REPORT.md`

---

**Admin Interface Version:** 1.0  
**Last Updated:** November 6, 2025  
**Status:** ✅ Fully Operational
