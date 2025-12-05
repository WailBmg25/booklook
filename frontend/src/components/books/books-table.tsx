"use client";

import { Book } from "@/types/api";
import { Star, BookOpen, Heart, Pen } from "lucide-react";
import Link from "next/link";
import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { favoritesApi } from "@/lib/api/favorites";
import BookCover from "./book-cover";

interface BooksTableProps {
  books: Book[];
  isLoading?: boolean;
  showFavoriteButton?: boolean;
  onFavoriteChange?: () => void;
}

export default function BooksTable({ 
  books, 
  isLoading,
  showFavoriteButton = false,
  onFavoriteChange
}: BooksTableProps) {
  const { data: session } = useSession();
  const [favorites, setFavorites] = useState<Set<number>>(new Set());
  const [loadingFavorites, setLoadingFavorites] = useState<Set<number>>(new Set());
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (session?.accessToken && showFavoriteButton) {
      loadFavorites();
    }
  }, [session, showFavoriteButton]);

  const loadFavorites = async () => {
    if (!session?.accessToken) return;
    try {
      const favoriteBooks = await favoritesApi.getFavorites(session.accessToken);
      setFavorites(new Set(favoriteBooks.map(book => book.id)));
    } catch (error: any) {
      // Silently fail if unauthorized (user needs to re-login)
      if (error.response?.status !== 401) {
        console.error("Failed to load favorites:", error);
      }
    }
  };

  const toggleFavorite = async (bookId: number, e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!session?.accessToken) return;
    
    setLoadingFavorites(prev => new Set(prev).add(bookId));
    
    try {
      if (favorites.has(bookId)) {
        await favoritesApi.removeFavorite(bookId, session.accessToken);
        setFavorites(prev => {
          const newSet = new Set(prev);
          newSet.delete(bookId);
          return newSet;
        });
      } else {
        await favoritesApi.addFavorite(bookId, session.accessToken);
        setFavorites(prev => new Set(prev).add(bookId));
      }
      onFavoriteChange?.();
    } catch (error) {
      console.error("Failed to toggle favorite:", error);
    } finally {
      setLoadingFavorites(prev => {
        const newSet = new Set(prev);
        newSet.delete(bookId);
        return newSet;
      });
    }
  };
  if (isLoading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div
            key={i}
            className="bg-white border border-gray-200 rounded-lg p-4 animate-pulse"
          >
            <div className="flex gap-4">
              <div className="w-16 h-24 bg-gray-200 rounded"></div>
              <div className="flex-1 space-y-2">
                <div className="h-6 bg-gray-200 rounded w-3/4"></div>
                <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                <div className="h-4 bg-gray-200 rounded w-full"></div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (books.length === 0) {
    return (
      <div className="text-center py-12 bg-white border border-gray-200 rounded-lg">
        <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">
          No books found
        </h3>
        <p className="text-gray-600">
          Try adjusting your search or filters to find what you're looking for.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {books.map((book) => (
        <Link
          key={book.id}
          href={`/books/${book.id}`}
          className="block bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
        >
          <div className="flex gap-4">
            {/* Book Cover */}
            <BookCover
              imageUrl={book.image_url}
              title={book.titre}
              size="small"
              className="flex-shrink-0"
            />

            {/* Book Info */}
            <div className="flex-1 min-w-0 flex justify-between items-start gap-4">
              <div className="flex-1 min-w-0">
              <h3 className="text-lg font-semibold text-gray-900 mb-1 truncate">
                {book.titre}
              </h3>

              <div className="flex items-center gap-1 text-sm text-gray-600 mb-2">
                <Pen className="h-3.5 w-3.5 text-gray-400" />
                <span>
                  {book.author_names && book.author_names.length > 0
                    ? book.author_names.join(", ")
                    : book.auteur || "Unknown Author"}
                </span>
                {book.date_publication ? (
                  <span className="text-gray-400">
                    {" "}
                    • {new Date(book.date_publication).getFullYear()}
                  </span>
                ) : (
                  <span className="text-gray-400"> • No publication date</span>
                )}
              </div>

              {book.description && (
                <p className="text-sm text-gray-700 line-clamp-2 mb-2">
                  {book.description}
                </p>
              )}

              <div className="flex items-center gap-4 text-sm">
                <div className="flex items-center gap-1">
                  <Star className={`h-4 w-4 ${
                    book.average_rating && book.average_rating > 0
                      ? "text-yellow-400 fill-yellow-400"
                      : "text-gray-300"
                  }`} />
                  <span className="font-medium">
                    {book.average_rating && book.average_rating > 0
                      ? book.average_rating.toFixed(1)
                      : "No rating"}
                  </span>
                  {book.review_count !== undefined && (
                    <span className="text-gray-500">
                      ({book.review_count} {book.review_count === 1 ? "review" : "reviews"})
                    </span>
                  )}
                </div>

                {book.nombre_pages && (
                  <span className="text-gray-500">
                    {book.nombre_pages} pages
                  </span>
                )}

                {book.langue && (
                  <span className="text-gray-500 uppercase">{book.langue}</span>
                )}
              </div>
              </div>

              {/* Favorite Button */}
              {mounted && showFavoriteButton && session && (
                <button
                  onClick={(e) => toggleFavorite(book.id, e)}
                  disabled={loadingFavorites.has(book.id)}
                  className="flex-shrink-0 p-2 rounded-full hover:bg-gray-100 transition-colors disabled:opacity-50"
                  title={favorites.has(book.id) ? "Remove from favorites" : "Add to favorites"}
                >
                  <Heart
                    className={`h-6 w-6 ${
                      favorites.has(book.id)
                        ? "text-red-600 fill-red-600"
                        : "text-gray-400"
                    }`}
                  />
                </button>
              )}
            </div>
          </div>
        </Link>
      ))}
    </div>
  );
}
