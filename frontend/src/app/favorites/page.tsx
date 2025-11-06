"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/navbar";
import BooksTable from "@/components/books/books-table";
import { favoritesApi } from "@/lib/api/favorites";
import { Book } from "@/types/api";
import { Heart } from "lucide-react";

export default function FavoritesPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [favorites, setFavorites] = useState<Book[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/auth/login");
    } else if (status === "authenticated" && session?.accessToken) {
      loadFavorites();
    }
  }, [status, session, router]);

  const loadFavorites = async () => {
    if (!session?.accessToken) return;

    setIsLoading(true);
    try {
      const data = await favoritesApi.getFavorites(session.accessToken);
      setFavorites(data);
    } catch (error) {
      console.error("Failed to load favorites:", error);
    } finally {
      setIsLoading(false);
    }
  };

  if (status === "loading" || isLoading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 rounded w-1/4"></div>
            <div className="h-64 bg-gray-200 rounded"></div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <Heart className="h-8 w-8 text-red-600 fill-red-600" />
            <h1 className="text-4xl font-bold text-gray-900">My Favorites</h1>
          </div>
          <p className="text-lg text-gray-600">
            {favorites.length === 0
              ? "You haven't added any favorites yet"
              : `${favorites.length} book${favorites.length !== 1 ? "s" : ""} in your favorites`}
          </p>
        </div>

        <BooksTable books={favorites} isLoading={false} />
      </main>
    </div>
  );
}
