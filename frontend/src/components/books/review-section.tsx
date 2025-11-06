"use client";

import { useState } from "react";
import { Star, Trash2 } from "lucide-react";
import { Review, CreateReviewRequest } from "@/types/api";
import { useSession } from "next-auth/react";
import { reviewsApi } from "@/lib/api/reviews";

interface ReviewSectionProps {
  bookId: number;
  reviews: Review[];
  onReviewAdded: () => void;
}

export default function ReviewSection({
  bookId,
  reviews,
  onReviewAdded,
}: ReviewSectionProps) {
  const { data: session } = useSession();
  const [showForm, setShowForm] = useState(false);
  const [rating, setRating] = useState(5);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session?.accessToken) return;

    setIsSubmitting(true);
    setError("");

    try {
      const reviewData: CreateReviewRequest = {
        rating,
        title: title || undefined,
        content: content || undefined,
      };

      await reviewsApi.createReview(bookId, reviewData, session.accessToken);

      // Reset form
      setRating(5);
      setTitle("");
      setContent("");
      setShowForm(false);
      onReviewAdded();
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Failed to submit review. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (reviewId: number) => {
    if (!session?.accessToken) return;
    if (!confirm("Are you sure you want to delete this review?")) return;

    try {
      await reviewsApi.deleteReview(reviewId, session.accessToken);
      onReviewAdded(); // Refresh reviews
    } catch (err) {
      console.error("Failed to delete review:", err);
    }
  };

  const renderStars = (count: number, interactive = false, onRate?: (rating: number) => void) => {
    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            onClick={() => interactive && onRate?.(star)}
            disabled={!interactive}
            className={interactive ? "cursor-pointer" : "cursor-default"}
          >
            <Star
              className={`h-5 w-5 ${
                star <= count
                  ? "text-yellow-400 fill-yellow-400"
                  : "text-gray-300"
              }`}
            />
          </button>
        ))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">
          Reviews ({reviews.length})
        </h2>
        {session && !showForm && (
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Write a Review
          </button>
        )}
      </div>

      {/* Review Form */}
      {showForm && session && (
        <form
          onSubmit={handleSubmit}
          className="bg-gray-50 border border-gray-200 rounded-lg p-6 space-y-4"
        >
          <h3 className="font-semibold text-gray-900">Write Your Review</h3>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Rating
            </label>
            {renderStars(rating, true, setRating)}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Title (optional)
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Sum up your review"
              className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white shadow-sm text-gray-900 placeholder-gray-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-900 mb-2">
              Review (optional)
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Share your thoughts about this book"
              rows={4}
              className="w-full px-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white shadow-sm text-gray-900 placeholder-gray-500"
            />
          </div>

          <div className="flex gap-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isSubmitting ? "Submitting..." : "Submit Review"}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowForm(false);
                setError("");
              }}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Reviews List */}
      <div className="space-y-4">
        {reviews.length === 0 ? (
          <p className="text-gray-600 text-center py-8">
            No reviews yet. Be the first to review this book!
          </p>
        ) : (
          reviews.map((review) => (
            <div
              key={review.id}
              className="bg-white border border-gray-200 rounded-lg p-4"
            >
              <div className="flex justify-between items-start mb-2">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    {renderStars(review.rating)}
                    <span className="text-sm text-gray-600">
                      {new Date(review.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  {review.user && (
                    <p className="text-sm font-medium text-gray-900">
                      {review.user.first_name} {review.user.last_name}
                    </p>
                  )}
                </div>
                {session?.user?.id === review.user_id.toString() && (
                  <button
                    onClick={() => handleDelete(review.id)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>

              {review.title && (
                <h4 className="font-semibold text-gray-900 mb-2">
                  {review.title}
                </h4>
              )}

              {review.content && (
                <p className="text-gray-700 whitespace-pre-wrap">
                  {review.content}
                </p>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
