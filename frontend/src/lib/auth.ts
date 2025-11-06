import NextAuth from "next-auth";
import Credentials from "next-auth/providers/credentials";
import { z } from "zod";
import { API_URL } from "./config";

const loginSchema = z.object({
  email: z.string({ message: "Email is required" }).regex(
    /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    "Invalid email address"
  ),
  password: z
    .string({ message: "Password is required" })
    .refine((val) => val.length >= 6, "Password must be at least 6 characters"),
});

// Helper function to get current user session (client-side)
export async function getCurrentUser() {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    const response = await fetch('/api/auth/session');
    if (!response.ok) {
      return null;
    }
    
    const session = await response.json();
    return session?.user || null;
  } catch (error) {
    console.error('Failed to get current user:', error);
    return null;
  }
}

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Credentials({
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      authorize: async (credentials) => {
        try {
          const { email, password } = loginSchema.parse(credentials);

          // Call backend API for authentication
          const response = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email, password }),
          });

          if (!response.ok) {
            console.error("Login failed:", response.status, await response.text());
            return null;
          }

          const data = await response.json();

          // Return user object with token (backend returns 'token' not 'access_token')
          return {
            id: data.user.id.toString(),
            email: data.user.email,
            name: `${data.user.first_name} ${data.user.last_name}`,
            accessToken: data.token,
            isAdmin: data.user.is_admin || false,
          };
        } catch (error) {
          console.error("Authentication error:", error);
          return null;
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.accessToken = user.accessToken;
        token.id = user.id;
        token.isAdmin = user.isAdmin;
      }
      return token;
    },
    async session({ session, token }) {
      if (token) {
        session.user.id = token.id as string;
        session.user.isAdmin = token.isAdmin as boolean;
        session.accessToken = token.accessToken as string;
      }
      return session;
    },
  },
  pages: {
    signIn: "/auth/login",
  },
  session: {
    strategy: "jwt",
    maxAge: 24 * 60 * 60, // 24 hours
  },
});
