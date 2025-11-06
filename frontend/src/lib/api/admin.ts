/**
 * Admin API client functions
 */

import { API_URL } from '../config';

const API_BASE_URL = API_URL;

// Helper function to get auth headers
async function getAuthHeaders(): Promise<HeadersInit> {
  // Get token from NextAuth session
  const sessionResponse = await fetch('/api/auth/session');
  const session = await sessionResponse.json();
  const token = session?.accessToken;
  
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
  };
}

// Analytics APIs
export async function getOverviewAnalytics() {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/analytics/overview`, {
    headers,
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch overview analytics');
  }
  
  return response.json();
}

export async function getUserAnalytics() {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/analytics/users`, {
    headers,
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch user analytics');
  }
  
  return response.json();
}

export async function getBookAnalytics() {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/analytics/books`, {
    headers,
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch book analytics');
  }
  
  return response.json();
}

export async function getReviewAnalytics() {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/analytics/reviews`, {
    headers,
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch review analytics');
  }
  
  return response.json();
}

// User Management APIs
export async function getUsers(params: {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean;
  is_admin?: boolean;
}) {
  const queryParams = new URLSearchParams();
  if (params.page) queryParams.append('page', params.page.toString());
  if (params.page_size) queryParams.append('page_size', params.page_size.toString());
  if (params.search) queryParams.append('search', params.search);
  if (params.is_active !== undefined) queryParams.append('is_active', params.is_active.toString());
  if (params.is_admin !== undefined) queryParams.append('is_admin', params.is_admin.toString());
  
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/users?${queryParams}`, {
    headers,
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch users');
  }
  
  return response.json();
}

export async function suspendUser(userId: number) {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/suspend`, {
    method: 'PUT',
    headers,
  });
  
  if (!response.ok) {
    throw new Error('Failed to suspend user');
  }
  
  return response.json();
}

export async function activateUser(userId: number) {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/activate`, {
    method: 'PUT',
    headers,
  });
  
  if (!response.ok) {
    throw new Error('Failed to activate user');
  }
  
  return response.json();
}

export async function deleteUser(userId: number) {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/users/${userId}`, {
    method: 'DELETE',
    headers,
  });
  
  if (!response.ok) {
    throw new Error('Failed to delete user');
  }
  
  return response.json();
}

export async function promoteToAdmin(userId: number) {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/promote`, {
    method: 'PUT',
    headers,
  });
  
  if (!response.ok) {
    throw new Error('Failed to promote user');
  }
  
  return response.json();
}

export async function revokeAdmin(userId: number) {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/revoke-admin`, {
    method: 'PUT',
    headers,
  });
  
  if (!response.ok) {
    throw new Error('Failed to revoke admin');
  }
  
  return response.json();
}

// Book Management APIs
export async function createBook(bookData: any) {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/books`, {
    method: 'POST',
    headers,
    body: JSON.stringify(bookData),
  });
  
  if (!response.ok) {
    throw new Error('Failed to create book');
  }
  
  return response.json();
}

export async function updateBook(bookId: number, bookData: any) {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/books/${bookId}`, {
    method: 'PUT',
    headers,
    body: JSON.stringify(bookData),
  });
  
  if (!response.ok) {
    throw new Error('Failed to update book');
  }
  
  return response.json();
}

export async function deleteBook(bookId: number) {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/books/${bookId}`, {
    method: 'DELETE',
    headers,
  });
  
  if (!response.ok) {
    throw new Error('Failed to delete book');
  }
  
  return response.json();
}

// Review Moderation APIs
export async function getReviews(params: {
  page?: number;
  page_size?: number;
  is_flagged?: boolean;
  book_id?: number;
  user_id?: number;
}) {
  const queryParams = new URLSearchParams();
  if (params.page) queryParams.append('page', params.page.toString());
  if (params.page_size) queryParams.append('page_size', params.page_size.toString());
  if (params.is_flagged !== undefined) queryParams.append('is_flagged', params.is_flagged.toString());
  if (params.book_id) queryParams.append('book_id', params.book_id.toString());
  if (params.user_id) queryParams.append('user_id', params.user_id.toString());
  
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/reviews?${queryParams}`, {
    headers,
  });
  
  if (!response.ok) {
    throw new Error('Failed to fetch reviews');
  }
  
  return response.json();
}

export async function getFlaggedReviews(page: number = 1, pageSize: number = 20) {
  const headers = await getAuthHeaders();
  const response = await fetch(
    `${API_BASE_URL}/admin/reviews/flagged?page=${page}&page_size=${pageSize}`,
    {
      headers,
    }
  );
  
  if (!response.ok) {
    throw new Error('Failed to fetch flagged reviews');
  }
  
  return response.json();
}

export async function flagReview(reviewId: number) {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/reviews/${reviewId}/flag`, {
    method: 'PUT',
    headers,
  });
  
  if (!response.ok) {
    throw new Error('Failed to flag review');
  }
  
  return response.json();
}

export async function approveReview(reviewId: number) {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/reviews/${reviewId}/approve`, {
    method: 'PUT',
    headers,
  });
  
  if (!response.ok) {
    throw new Error('Failed to approve review');
  }
  
  return response.json();
}

export async function deleteReview(reviewId: number) {
  const headers = await getAuthHeaders();
  const response = await fetch(`${API_BASE_URL}/admin/reviews/${reviewId}`, {
    method: 'DELETE',
    headers,
  });
  
  if (!response.ok) {
    throw new Error('Failed to delete review');
  }
  
  return response.json();
}
