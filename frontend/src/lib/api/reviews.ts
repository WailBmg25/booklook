import apiClient from "@/lib/api-client";
import { Review, CreateReviewRequest } from "@/types/api";

export const reviewsApi = {
  async getBookReviews(
    bookId: number,
    accessToken?: string
  ): Promise<Review[]> {
    const config = accessToken
      ? { headers: { Authorization: `Bearer ${accessToken}` } }
      : {};

    const response = await apiClient.get(
      `/books/${bookId}/reviews`,
      config
    );
    // Backend returns { reviews: [], pagination: {} }
    return response.data.reviews || [];
  },

  async createReview(
    bookId: number,
    review: CreateReviewRequest,
    accessToken: string
  ): Promise<Review> {
    const response = await apiClient.post(
      `/reviews/books/${bookId}`,
      review,
      {
        headers: { Authorization: `Bearer ${accessToken}` },
      }
    );
    return response.data;
  },

  async deleteReview(reviewId: number, accessToken: string): Promise<void> {
    await apiClient.delete(`/reviews/${reviewId}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  },
};
