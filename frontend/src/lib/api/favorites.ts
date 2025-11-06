import apiClient from "@/lib/api-client";
import { Book } from "@/types/api";

export const favoritesApi = {
  async getFavorites(accessToken: string): Promise<Book[]> {
    const response = await apiClient.get("/user/favorites", {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
    // Backend returns { books: [], pagination: {} }
    return response.data.books || [];
  },

  async addFavorite(bookId: number, accessToken: string): Promise<void> {
    await apiClient.post(
      `/user/favorites/${bookId}`,
      {},
      {
        headers: { Authorization: `Bearer ${accessToken}` },
      }
    );
  },

  async removeFavorite(bookId: number, accessToken: string): Promise<void> {
    await apiClient.delete(`/user/favorites/${bookId}`, {
      headers: { Authorization: `Bearer ${accessToken}` },
    });
  },

  async isFavorite(bookId: number, accessToken: string): Promise<boolean> {
    try {
      const response = await apiClient.get(`/user/favorites/${bookId}/check`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      return response.data.is_favorited; // Backend returns 'is_favorited' not 'is_favorite'
    } catch (error) {
      return false;
    }
  },
};
