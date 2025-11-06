"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import Navbar from "@/components/navbar";
import BookFiltersComponent from "@/components/books/book-filters";
import BooksTable from "@/components/books/books-table";
import Pagination from "@/components/books/pagination";
import { booksApi } from "@/lib/api/books";
import { Book, BookFilters, PaginatedBooks } from "@/types/api";

export default function Home() {
  const { data: session } = useSession();
  const [books, setBooks] = useState<Book[]>([]);
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 0,
  });
  const [filters, setFilters] = useState<BookFilters>({});
  const [isLoading, setIsLoading] = useState(true);
  const [genres, setGenres] = useState<string[]>([]);
  const [authors, setAuthors] = useState<string[]>([]);

  useEffect(() => {
    loadBooks();
  }, [pagination.page, filters, session]);

  useEffect(() => {
    loadGenresAndAuthors();
  }, [session]);

  const loadBooks = async () => {
    setIsLoading(true);
    try {
      const data: PaginatedBooks = await booksApi.getBooks(
        pagination.page,
        pagination.pageSize,
        filters,
        session?.accessToken
      );

      setBooks(data.items);
      setPagination((prev) => ({
        ...prev,
        total: data.total,
        totalPages: data.total_pages,
      }));
    } catch (error) {
      console.error("Failed to load books:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadGenresAndAuthors = async () => {
    try {
      const [genresData, authorsData] = await Promise.all([
        booksApi.getGenres(session?.accessToken),
        booksApi.getAuthors(session?.accessToken),
      ]);
      setGenres(genresData);
      setAuthors(authorsData);
    } catch (error) {
      console.error("Failed to load filters:", error);
    }
  };

  const handleFiltersChange = (newFilters: BookFilters) => {
    setFilters(newFilters);
    setPagination((prev) => ({ ...prev, page: 1 }));
  };

  const handlePageChange = (page: number) => {
    setPagination((prev) => ({ ...prev, page }));
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Discover Books
          </h1>
          <p className="text-lg text-gray-600">
            Browse our extensive collection of books
          </p>
        </div>

        <BookFiltersComponent
          filters={filters}
          onFiltersChange={handleFiltersChange}
          genres={genres}
          authors={authors}
        />

        <div className="mt-6">
          {!isLoading && (
            <p className="text-sm text-gray-600 mb-4">
              Showing {books.length} of {pagination.total} books
            </p>
          )}

          <BooksTable 
            books={books} 
            isLoading={isLoading} 
            showFavoriteButton={true}
            onFavoriteChange={loadBooks}
          />

          <Pagination
            currentPage={pagination.page}
            totalPages={pagination.totalPages}
            onPageChange={handlePageChange}
          />
        </div>
      </main>
    </div>
  );
}
