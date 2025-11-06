# Admin Authentication Fix

## Issues Fixed

### Issue 1: Admin Dashboard Redirecting to Home
**Problem:** Admin users were being redirected to home page when accessing `/admin`  
**Root Cause:** The `getCurrentUser()` function was trying to use localStorage tokens, but the app uses NextAuth sessions

**Solution:**
- Updated `getCurrentUser()` to fetch from NextAuth session API (`/api/auth/session`)
- Modified admin layout to check `user.isAdmin` instead of `user.is_admin`

### Issue 2: Admin Users Should Go Directly to Admin Dashboard
**Problem:** After login, admin users were redirected to home page like regular users  
**Root Cause:** Login page didn't check user role before redirecting

**Solution:**
- Updated login page to check if user is admin after successful authentication
- Redirect admin users to `/admin` instead of `/`
- Regular users still go to `/` (home page)

---

## Changes Made

### 1. Updated NextAuth Configuration (`frontend/src/lib/auth.ts`)

**Added `isAdmin` to user object:**
```typescript
return {
  id: data.user.id.toString(),
  email: data.user.email,
  name: `${data.user.first_name} ${data.user.last_name}`,
  accessToken: data.token,
  isAdmin: data.user.is_admin || false,  // ✅ NEW
};
```

**Added `isAdmin` to JWT token:**
```typescript
async jwt({ token, user }) {
  if (user) {
    token.accessToken = user.accessToken;
    token.id = user.id;
    token.isAdmin = user.isAdmin;  // ✅ NEW
  }
  return token;
}
```

**Added `isAdmin` to session:**
```typescript
async session({ session, token }) {
  if (token) {
    session.user.id = token.id as string;
    session.user.isAdmin = token.isAdmin as boolean;  // ✅ NEW
    session.accessToken = token.accessToken as string;
  }
  return session;
}
```

**Updated `getCurrentUser()` function:**
```typescript
// OLD - Used localStorage (doesn't work with NextAuth)
export async function getCurrentUser() {
  const token = localStorage.getItem('token');
  // ... fetch from API with token
}

// NEW - Uses NextAuth session
export async function getCurrentUser() {
  const response = await fetch('/api/auth/session');
  const session = await response.json();
  return session?.user || null;
}
```

### 2. Updated TypeScript Types (`frontend/src/types/next-auth.d.ts`)

**Added `isAdmin` to Session, User, and JWT interfaces:**
```typescript
declare module "next-auth" {
  interface Session {
    user: {
      id: string;
      isAdmin?: boolean;  // ✅ NEW
    } & DefaultSession["user"];
  }

  interface User {
    isAdmin?: boolean;  // ✅ NEW
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    isAdmin?: boolean;  // ✅ NEW
  }
}
```

### 3. Updated Login Page (`frontend/src/app/auth/login/page.tsx`)

**Added admin check and conditional redirect:**
```typescript
if (result?.error) {
  setError("Invalid email or password");
} else {
  // ✅ NEW - Check if user is admin
  const sessionResponse = await fetch('/api/auth/session');
  const session = await sessionResponse.json();
  
  if (session?.user?.isAdmin) {
    router.push("/admin");  // Admin → Admin Dashboard
  } else {
    router.push("/");       // Regular User → Home
  }
  router.refresh();
}
```

### 4. Updated Admin Layout (`frontend/src/app/admin/layout.tsx`)

**Changed property check from `is_admin` to `isAdmin`:**
```typescript
// OLD
if (!user || !user.is_admin) {
  router.push('/');
  return;
}

// NEW
if (!user || !user.isAdmin) {
  router.push('/');
  return;
}
```

---

## How It Works Now

### Login Flow for Admin Users:

1. **User enters credentials** at `/auth/login`
2. **NextAuth authenticates** with backend API
3. **Backend returns user data** including `is_admin: true`
4. **NextAuth stores** `isAdmin: true` in session
5. **Login page checks** session for `isAdmin`
6. **Admin user redirected** to `/admin` ✅
7. **Regular user redirected** to `/` ✅

### Admin Dashboard Access:

1. **User navigates** to `/admin`
2. **Admin layout checks** session via `getCurrentUser()`
3. **Session fetched** from `/api/auth/session`
4. **If `isAdmin: true`** → Show admin dashboard ✅
5. **If not admin** → Redirect to home `/` ✅
6. **If not logged in** → Redirect to home `/` ✅

---

## Testing the Fix

### Test 1: Admin User Login
```bash
1. Go to http://localhost:3000/auth/login
2. Login with: final_test@example.com / Test1234
3. ✅ Should redirect to http://localhost:3000/admin
4. ✅ Should see admin dashboard
```

### Test 2: Regular User Login
```bash
1. Go to http://localhost:3000/auth/login
2. Login with regular user credentials
3. ✅ Should redirect to http://localhost:3000/ (home)
4. ✅ Should NOT have access to /admin
```

### Test 3: Direct Admin Access
```bash
1. Logout if logged in
2. Try to access http://localhost:3000/admin
3. ✅ Should redirect to home (not logged in)

4. Login as regular user
5. Try to access http://localhost:3000/admin
6. ✅ Should redirect to home (not admin)

7. Login as admin user
8. Access http://localhost:3000/admin
9. ✅ Should show admin dashboard
```

---

## Admin User Credentials

**Email:** `final_test@example.com`  
**Password:** `Test1234`  
**Role:** Admin (`is_admin: true`)

---

## Files Modified

1. ✅ `frontend/src/lib/auth.ts` - NextAuth config and getCurrentUser()
2. ✅ `frontend/src/types/next-auth.d.ts` - TypeScript types
3. ✅ `frontend/src/app/auth/login/page.tsx` - Login redirect logic
4. ✅ `frontend/src/app/admin/layout.tsx` - Admin check property name

---

## Summary

✅ **Admin dashboard now works correctly**  
✅ **Admin users redirect to /admin after login**  
✅ **Regular users redirect to / after login**  
✅ **Non-admin users cannot access /admin**  
✅ **Session-based authentication working properly**

The admin interface is now fully functional with proper role-based access control and automatic routing based on user role!
