# Frontend Setup Guide

## Prerequisites

- Node.js 18+ installed
- Backend API running on `http://localhost:8000`

## Installation

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Configure environment variables:
```bash
cp .env.local.example .env.local
```

Edit `.env.local` and update:
- `NEXTAUTH_SECRET`: Generate a secure random string
- `NEXT_PUBLIC_API_URL`: Backend API URL (default: http://localhost:8000)

## Running the Development Server

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Features Implemented

### Authentication (Task 4.1)
- NextAuth.js v5 with credentials provider
- Login page: `/auth/login`
- Registration page: `/auth/register`
- Protected routes with proxy middleware
- JWT session management

### Books Listing & Filtering (Task 4.2)
- Responsive books table with pagination
- Real-time search by title, author, or keyword
- Filter by genre, author, and minimum rating
- Sort by title, author, rating, or publication date
- Pagination with page navigation

### Book Details & Reviews (Task 4.3)
- Detailed book information page
- Star rating display and average ratings
- Review submission form for authenticated users
- Review listing with user information
- Favorites functionality (add/remove)
- Favorites page showing all user's favorite books

### Reading Interface (Task 4.4)
- Full-screen reading mode with smooth scrolling
- Reading progress tracking (percentage and page number)
- Progress bar visualization
- Light/dark theme toggle
- Font size adjustment (small, medium, large)
- Auto-save reading position every 30 seconds
- Resume reading from last position

## Project Structure

```
frontend/
├── src/
│   ├── app/                           # Next.js app directory
│   │   ├── api/auth/[...nextauth]/   # NextAuth API routes
│   │   ├── auth/                      # Authentication pages
│   │   │   ├── login/page.tsx
│   │   │   └── register/page.tsx
│   │   ├── books/[id]/page.tsx       # Book details page
│   │   ├── read/[id]/page.tsx        # Reading interface
│   │   ├── favorites/page.tsx        # Favorites page
│   │   ├── layout.tsx                # Root layout
│   │   └── page.tsx                  # Home page (books listing)
│   ├── components/                    # React components
│   │   ├── books/
│   │   │   ├── book-filters.tsx      # Search and filter component
│   │   │   ├── books-table.tsx       # Books list display
│   │   │   ├── pagination.tsx        # Pagination component
│   │   │   └── review-section.tsx    # Reviews display and form
│   │   ├── navbar.tsx                # Navigation bar
│   │   └── providers.tsx             # Client-side providers
│   ├── lib/                          # Utilities
│   │   ├── api/                      # API service functions
│   │   │   ├── books.ts
│   │   │   ├── reviews.ts
│   │   │   ├── favorites.ts
│   │   │   └── reading-progress.ts
│   │   ├── auth.ts                   # NextAuth configuration
│   │   └── api-client.ts             # Axios API client
│   ├── types/                        # TypeScript types
│   │   ├── api.ts                    # API response types
│   │   └── next-auth.d.ts            # NextAuth type extensions
│   └── proxy.ts                      # Route protection proxy
├── .env.local                        # Environment variables
└── package.json
```

## API Integration

The frontend integrates with the following backend endpoints:

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login

### Books
- `GET /books` - List books with filters and pagination
- `GET /books/{id}` - Get book details
- `GET /books/genres` - Get available genres
- `GET /books/authors` - Get available authors

### Reviews
- `GET /books/{id}/reviews` - Get book reviews
- `POST /books/{id}/reviews` - Create review
- `DELETE /reviews/{id}` - Delete review

### Favorites
- `GET /user/favorites` - Get user's favorites
- `POST /user/favorites/{id}` - Add to favorites
- `DELETE /user/favorites/{id}` - Remove from favorites
- `GET /user/favorites/{id}` - Check if book is favorite

### Reading Progress
- `GET /user/reading-progress/{id}` - Get reading progress
- `PUT /user/reading-progress/{id}` - Update reading progress

## Technology Stack

- **Framework**: Next.js 16 with App Router
- **Authentication**: NextAuth.js v5
- **Styling**: Tailwind CSS v4
- **Forms**: React Hook Form with Zod v4 validation
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **TypeScript**: v5

## Status

✅ Task 4.1: Next.js project structure and authentication - COMPLETE
✅ Task 4.2: Books listing and filtering interface - COMPLETE
✅ Task 4.3: Book details and review interface - COMPLETE
✅ Task 4.4: Scrolling reading interface - COMPLETE

All frontend tasks for Phase 4 are now complete!
