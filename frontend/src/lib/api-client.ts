import axios from "axios";
import { API_URL } from "./config";
import { signOut } from "next-auth/react";

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add request interceptor to include auth token
apiClient.interceptors.request.use(
  (config) => {
    // Token will be added from session in components
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Session expired or invalid - automatically log out user
      if (typeof window !== 'undefined') {
        await signOut({ callbackUrl: '/auth/login?expired=true' });
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
