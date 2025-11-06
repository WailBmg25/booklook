import apiClient from "@/lib/api-client";
import { ReadingProgress, UpdateProgressRequest } from "@/types/api";

export const readingProgressApi = {
  async getProgress(
    bookId: number,
    accessToken: string
  ): Promise<ReadingProgress | null> {
    try {
      const response = await apiClient.get(
        `/user/reading-progress/${bookId}`,
        {
          headers: { Authorization: `Bearer ${accessToken}` },
        }
      );
      return response.data;
    } catch (error) {
      return null;
    }
  },

  async updateProgress(
    bookId: number,
    progress: UpdateProgressRequest,
    accessToken: string
  ): Promise<ReadingProgress> {
    const response = await apiClient.put(
      `/user/reading-progress/${bookId}`,
      progress,
      {
        headers: { Authorization: `Bearer ${accessToken}` },
      }
    );
    return response.data;
  },
};
