import apiClient from "@/lib/api-client";
import { Book, PaginatedBooks, BookFilters, BookContent } from "@/types/api";

export const booksApi = {
  async getBooks(
    page: number = 1,
    pageSize: number = 20,
    filters?: BookFilters,
    accessToken?: string
  ): Promise<PaginatedBooks> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });

    if (filters?.search) params.append("search", filters.search);
    if (filters?.genre) params.append("genre_filter", filters.genre);
    if (filters?.author) params.append("author_filter", filters.author);
    if (filters?.min_rating)
      params.append("min_rating", filters.min_rating.toString());
    
    // Map frontend sort fields to backend fields
    if (filters?.sort_by) {
      const sortByMap: Record<string, string> = {
        title: "titre",
        author: "titre", // Backend doesn't support author sort, use title
        rating: "average_rating",
        date_publication: "date_publication",
      };
      params.append("sort_by", sortByMap[filters.sort_by] || filters.sort_by);
    }
    
    if (filters?.sort_order) params.append("sort_order", filters.sort_order);

    const config = accessToken
      ? { headers: { Authorization: `Bearer ${accessToken}` } }
      : {};

    const response = await apiClient.get(`/books?${params.toString()}`, config);
    
    // Transform backend response to match frontend types
    return {
      items: response.data.books || [],
      total: response.data.pagination?.total_count || 0,
      page: response.data.pagination?.current_page || page,
      page_size: response.data.pagination?.page_size || pageSize,
      total_pages: response.data.pagination?.total_pages || 0,
    };
  },

  async getBook(bookId: number, accessToken?: string): Promise<Book> {
    const config = accessToken
      ? { headers: { Authorization: `Bearer ${accessToken}` } }
      : {};

    const response = await apiClient.get(`/books/${bookId}`, config);
    return response.data;
  },

  async getGenres(accessToken?: string): Promise<string[]> {
    const config = accessToken
      ? { headers: { Authorization: `Bearer ${accessToken}` } }
      : {};

    const response = await apiClient.get("/books/metadata/genres", config);
    return response.data;
  },

  async getAuthors(accessToken?: string): Promise<string[]> {
    const config = accessToken
      ? { headers: { Authorization: `Bearer ${accessToken}` } }
      : {};

    const response = await apiClient.get("/books/metadata/authors", config);
    return response.data;
  },

  async getBookContent(
    bookId: number,
    page: number = 1,
    wordsPerPage: number = 300,
    accessToken?: string
  ): Promise<BookContent> {
    const config = accessToken
      ? { headers: { Authorization: `Bearer ${accessToken}` } }
      : {};

    const response = await apiClient.get(
      `/books/${bookId}/content/page/${page}?words_per_page=${wordsPerPage}`,
      config
    );
    return response.data;
  },
};
