'use client';

import { useEffect, useState } from 'react';
import { getReviews, getFlaggedReviews, flagReview, approveReview, deleteReview } from '@/lib/api/admin';

export default function AdminReviewsPage() {
  const [reviews, setReviews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showFlaggedOnly, setShowFlaggedOnly] = useState(false);

  const fetchReviews = async () => {
    setLoading(true);
    try {
      const data = showFlaggedOnly
        ? await getFlaggedReviews(page, 20)
        : await getReviews({ page, page_size: 20 });
      
      setReviews(data.reviews);
      setTotalPages(data.total_pages);
    } catch (error) {
      console.error('Failed to fetch reviews:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, [page, showFlaggedOnly]);

  const handleFlag = async (reviewId: number) => {
    try {
      await flagReview(reviewId);
      fetchReviews();
    } catch (error) {
      alert('Failed to flag review');
    }
  };

  const handleApprove = async (reviewId: number) => {
    try {
      await approveReview(reviewId);
      fetchReviews();
    } catch (error) {
      alert('Failed to approve review');
    }
  };

  const handleDelete = async (reviewId: number) => {
    if (!confirm('Are you sure you want to delete this review? This action cannot be undone.')) return;
    
    try {
      await deleteReview(reviewId);
      fetchReviews();
    } catch (error) {
      alert('Failed to delete review');
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Review Moderation</h1>
        <p className="mt-2 text-gray-600">Manage and moderate user reviews</p>
      </div>

      {/* Filter */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex gap-4">
          <button
            onClick={() => {
              setShowFlaggedOnly(false);
              setPage(1);
            }}
            className={`px-4 py-2 rounded-lg ${!showFlaggedOnly ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
          >
            All Reviews
          </button>
          <button
            onClick={() => {
              setShowFlaggedOnly(true);
              setPage(1);
            }}
            className={`px-4 py-2 rounded-lg ${showFlaggedOnly ? 'bg-red-600 text-white' : 'bg-gray-200'}`}
          >
            Flagged Reviews
          </button>
        </div>
      </div>

      {/* Reviews List */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : reviews.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500">No reviews found</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reviews.map((review) => (
            <div key={review.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  {/* Review Header */}
                  <div className="flex items-center gap-4 mb-3">
                    <div className="flex items-center">
                      {[...Array(5)].map((_, i) => (
                        <span key={i} className={i < review.rating ? 'text-yellow-500' : 'text-gray-300'}>
                          ⭐
                        </span>
                      ))}
                    </div>
                    {review.is_flagged && (
                      <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full">
                        Flagged
                      </span>
                    )}
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      review.sentiment === 'positive' ? 'bg-green-100 text-green-800' :
                      review.sentiment === 'negative' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {review.sentiment}
                    </span>
                  </div>

                  {/* Review Title */}
                  {review.title && (
                    <h3 className="text-lg font-semibold mb-2">{review.title}</h3>
                  )}

                  {/* Review Content */}
                  <p className="text-gray-700 mb-3">{review.content || 'No content'}</p>

                  {/* Review Meta */}
                  <div className="flex items-center gap-4 text-sm text-gray-500">
                    <span>By: {review.user?.display_name || 'Unknown'}</span>
                    <span>•</span>
                    <span>Book: {review.book?.titre || 'Unknown'}</span>
                    <span>•</span>
                    <span>{new Date(review.created_at).toLocaleDateString()}</span>
                    <span>•</span>
                    <span>{review.word_count} words</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-2 ml-4">
                  {review.is_flagged ? (
                    <button
                      onClick={() => handleApprove(review.id)}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 text-sm"
                    >
                      Approve
                    </button>
                  ) : (
                    <button
                      onClick={() => handleFlag(review.id)}
                      className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 text-sm"
                    >
                      Flag
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(review.id)}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 text-sm"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 bg-white border rounded-lg disabled:opacity-50"
          >
            Previous
          </button>
          <span className="px-4 py-2">
            Page {page} of {totalPages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
            disabled={page === totalPages}
            className="px-4 py-2 bg-white border rounded-lg disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
