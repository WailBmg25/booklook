// User types
export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  created_at: string;
  is_active: boolean;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Book types
export interface Book {
  id: number;
  titre: string;
  isbn?: string;
  image_url?: string;
  auteur?: string;
  author_names?: string[];
  genre_names?: string[];
  editeur?: string;
  date_publication?: string;
  langue?: string;
  nombre_pages?: number;
  total_pages?: number;
  description?: string;
  average_rating?: number;
  review_count?: number;
  created_at: string;
}

export interface PaginatedBooks {
  items: Book[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Review types
export interface Review {
  id: number;
  user_id: number;
  book_id: number;
  rating: number;
  title?: string;
  content?: string;
  created_at: string;
  updated_at?: string;
  user?: {
    first_name: string;
    last_name: string;
  };
}

export interface CreateReviewRequest {
  rating: number;
  title?: string;
  content?: string;
}

// Reading Progress types
export interface ReadingProgress {
  user_id: number;
  book_id: number;
  current_page: number;
  total_pages: number;
  last_read_at: string;
  progress_percentage: number;
}

export interface UpdateProgressRequest {
  current_page: number;
}

// Filter types
export interface BookFilters {
  search?: string;
  genre?: string;
  author?: string;
  min_rating?: number;
  sort_by?: "title" | "author" | "rating" | "date_publication";
  sort_order?: "asc" | "desc";
}

// Book Content types
export interface BookContent {
  book_id: number;
  book_title: string;
  page: number;
  total_pages: number;
  content: string;
  has_next: boolean;
  has_previous: boolean;
}
