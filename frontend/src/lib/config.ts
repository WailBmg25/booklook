/**
 * Frontend configuration
 * Centralized configuration for API endpoints and app settings
 */

// Backend API base URL (from environment variable)
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// API version prefix
export const API_VERSION = "/api/v1";

// Full API URL with version
export const API_URL = `${API_BASE_URL}${API_VERSION}`;

// NextAuth configuration
export const NEXTAUTH_URL = process.env.NEXTAUTH_URL || "http://localhost:3000";

// App configuration
export const APP_NAME = "BookLook";
export const APP_DESCRIPTION = "Your Digital Library";

// Pagination defaults
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;

// Session configuration
export const SESSION_MAX_AGE = 24 * 60 * 60; // 24 hours in seconds
