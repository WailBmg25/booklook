"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import Link from "next/link";
import {
  BookOpen,
  Star,
  Heart,
  ArrowLeft,
  Calendar,
  FileText,
  Globe,
} from "lucide-react";
import Navbar from "@/components/navbar";
import ReviewSection from "@/components/books/review-section";
import { booksApi } from "@/lib/api/books";
import { reviewsApi } from "@/lib/api/reviews";
import { favoritesApi } from "@/lib/api/favorites";
import { Book, Review } from "@/types/api";

export default function BookDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const { data: session } = useSession();
  const bookId = parseInt(params.id as string);

  const [book, setBook] = useState<Book | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [isFavorite, setIsFavorite] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isFavoriteLoading, setIsFavoriteLoading] = useState(false);

  useEffect(() => {
    loadBookDetails();
    loadReviews();
    if (session?.accessToken) {
      checkFavoriteStatus();
    }
  }, [bookId, session]);

  const loadBookDetails = async () => {
    try {
      const data = await booksApi.getBook(bookId, session?.accessToken);
      setBook(data);
    } catch (error) {
      console.error("Failed to load book:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadReviews = async () => {
    try {
      const data = await reviewsApi.getBookReviews(
        bookId,
        session?.accessToken
      );
      setReviews(data);
    } catch (error) {
      console.error("Failed to load reviews:", error);
    }
  };

  const checkFavoriteStatus = async () => {
    if (!session?.accessToken) return;
    try {
      const status = await favoritesApi.isFavorite(
        bookId,
        session.accessToken
      );
      setIsFavorite(status);
    } catch (error) {
      console.error("Failed to check favorite status:", error);
    }
  };

  const toggleFavorite = async () => {
    if (!session?.accessToken) {
      router.push("/auth/login");
      return;
    }

    setIsFavoriteLoading(true);
    try {
      if (isFavorite) {
        await favoritesApi.removeFavorite(bookId, session.accessToken);
        setIsFavorite(false);
      } else {
        await favoritesApi.addFavorite(bookId, session.accessToken);
        setIsFavorite(true);
      }
    } catch (error) {
      console.error("Failed to toggle favorite:", error);
    } finally {
      setIsFavoriteLoading(false);
    }
  };

  const handleReviewAdded = async () => {
    // Reload reviews immediately
    await loadReviews();
    // Wait a moment for backend cache to update, then reload book details
    setTimeout(async () => {
      await loadBookDetails();
    }, 1000);
  };

  if (isLoading) {
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

  if (!book) {
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center py-12">
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              Book not found
            </h1>
            <Link
              href="/"
              className="text-blue-600 hover:text-blue-700 flex items-center justify-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to books
            </Link>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Link
          href="/"
          className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 mb-6"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to books
        </Link>

        {/* Book Header */}
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <div className="flex gap-6">
            {/* Book Cover */}
            <div className="flex-shrink-0 w-32 h-48 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <BookOpen className="h-16 w-16 text-white" />
            </div>

            {/* Book Info */}
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {book.titre}
              </h1>

              <p className="text-lg text-gray-600 mb-4">
                {book.author_names && book.author_names.length > 0
                  ? book.author_names.join(", ")
                  : "Unknown Author"}
              </p>

              {/* Rating */}
              <div className="flex items-center gap-2 mb-4">
                <div className="flex items-center gap-1">
                  <Star className={`h-5 w-5 ${
                    book.average_rating && book.average_rating > 0
                      ? "text-yellow-400 fill-yellow-400"
                      : "text-gray-300"
                  }`} />
                  <span className="text-xl font-semibold">
                    {book.average_rating && book.average_rating > 0
                      ? book.average_rating.toFixed(1)
                      : "No rating"}
                  </span>
                </div>
                <span className="text-gray-600">
                  ({reviews.length} {reviews.length === 1 ? "review" : "reviews"})
                </span>
              </div>

              {/* Metadata */}
              <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                {book.date_publication && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <Calendar className="h-4 w-4" />
                    <span>
                      Published:{" "}
                      {new Date(book.date_publication).getFullYear()}
                    </span>
                  </div>
                )}
                {book.nombre_pages && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <FileText className="h-4 w-4" />
                    <span>{book.nombre_pages} pages</span>
                  </div>
                )}
                {book.langue && (
                  <div className="flex items-center gap-2 text-gray-600">
                    <Globe className="h-4 w-4" />
                    <span className="uppercase">{book.langue}</span>
                  </div>
                )}
                {book.isbn && (
                  <div className="text-gray-600">
                    <span className="font-medium">ISBN:</span> {book.isbn}
                  </div>
                )}
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <Link
                  href={`/read/${book.id}`}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
                >
                  <BookOpen className="h-5 w-5" />
                  Read Book
                </Link>
                <button
                  onClick={toggleFavorite}
                  disabled={isFavoriteLoading}
                  className={`px-6 py-2 rounded-lg flex items-center gap-2 ${
                    isFavorite
                      ? "bg-red-50 text-red-600 border border-red-200 hover:bg-red-100"
                      : "bg-gray-50 text-gray-700 border border-gray-300 hover:bg-gray-100"
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  <Heart
                    className={`h-5 w-5 ${isFavorite ? "fill-red-600" : ""}`}
                  />
                  {isFavorite ? "Remove from Favorites" : "Add to Favorites"}
                </button>
              </div>
            </div>
          </div>

          {/* Description */}
          {book.description && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h2 className="text-xl font-bold text-gray-900 mb-3">
                Description
              </h2>
              <p className="text-gray-700 whitespace-pre-wrap">
                {book.description}
              </p>
            </div>
          )}
        </div>

        {/* Reviews Section */}
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <ReviewSection
            bookId={bookId}
            reviews={reviews}
            onReviewAdded={handleReviewAdded}
          />
        </div>
      </main>
    </div>
  );
}
