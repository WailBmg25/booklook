"use client";

import { useState } from "react";
import { Search, Filter, X } from "lucide-react";
import { BookFilters } from "@/types/api";

interface BookFiltersProps {
  filters: BookFilters;
  onFiltersChange: (filters: BookFilters) => void;
  genres?: string[];
  authors?: string[];
}

export default function BookFiltersComponent({
  filters,
  onFiltersChange,
  genres = [],
  authors = [],
}: BookFiltersProps) {
  const [showFilters, setShowFilters] = useState(false);

  const handleSearchChange = (value: string) => {
    onFiltersChange({ ...filters, search: value || undefined });
  };

  const handleGenreChange = (value: string) => {
    onFiltersChange({ ...filters, genre: value || undefined });
  };

  const handleAuthorChange = (value: string) => {
    onFiltersChange({ ...filters, author: value || undefined });
  };

  const handleRatingChange = (value: string) => {
    onFiltersChange({
      ...filters,
      min_rating: value ? parseFloat(value) : undefined,
    });
  };

  const handleSortChange = (
    sortBy: BookFilters["sort_by"],
    sortOrder: BookFilters["sort_order"]
  ) => {
    onFiltersChange({ ...filters, sort_by: sortBy, sort_order: sortOrder });
  };

  const clearFilters = () => {
    onFiltersChange({});
  };

  const hasActiveFilters =
    filters.search ||
    filters.genre ||
    filters.author ||
    filters.min_rating ||
    filters.sort_by;

  return (
    <div className="space-y-4">
      {/* Search Bar */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-blue-600" />
          <input
            type="text"
            placeholder="Search books by title, author, or keyword..."
            value={filters.search || ""}
            onChange={(e) => handleSearchChange(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white shadow-sm text-gray-900 placeholder-gray-500"
          />
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 px-4 py-2.5 border-2 border-blue-600 rounded-lg hover:bg-blue-600 hover:text-white bg-white shadow-sm font-medium text-blue-600 transition-colors"
        >
          <Filter className="h-5 w-5" />
          <span>Filters</span>
          {hasActiveFilters && (
            <span className="bg-blue-600 text-white text-xs rounded-full px-2 py-0.5">
              Active
            </span>
          )}
        </button>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
          <div className="flex justify-between items-center">
            <h3 className="font-semibold text-gray-900">Filters</h3>
            {hasActiveFilters && (
              <button
                onClick={clearFilters}
                className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
              >
                <X className="h-4 w-4" />
                Clear all
              </button>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Genre Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-1">
                Genre
              </label>
              <select
                value={filters.genre || ""}
                onChange={(e) => handleGenreChange(e.target.value)}
                className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 shadow-sm"
              >
                <option value="">All Genres</option>
                {genres.map((genre) => (
                  <option key={genre} value={genre}>
                    {genre}
                  </option>
                ))}
              </select>
            </div>

            {/* Author Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-1">
                Author
              </label>
              <select
                value={filters.author || ""}
                onChange={(e) => handleAuthorChange(e.target.value)}
                className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 shadow-sm"
              >
                <option value="">All Authors</option>
                {authors.slice(0, 100).map((author) => (
                  <option key={author} value={author}>
                    {author}
                  </option>
                ))}
              </select>
            </div>

            {/* Rating Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-900 mb-1">
                Minimum Rating
              </label>
              <select
                value={filters.min_rating?.toString() || ""}
                onChange={(e) => handleRatingChange(e.target.value)}
                className="w-full px-3 py-2 border-2 border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 shadow-sm"
              >
                <option value="">Any Rating</option>
                <option value="4">4+ Stars</option>
                <option value="3">3+ Stars</option>
                <option value="2">2+ Stars</option>
              </select>
            </div>
          </div>

          {/* Sort Options */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Sort By
            </label>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => handleSortChange("title", "asc")}
                className={`px-3 py-1.5 rounded-lg text-sm ${
                  filters.sort_by === "title" && filters.sort_order === "asc"
                    ? "bg-blue-600 text-white"
                    : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
                }`}
              >
                Title (A-Z)
              </button>
              <button
                onClick={() => handleSortChange("author", "asc")}
                className={`px-3 py-1.5 rounded-lg text-sm ${
                  filters.sort_by === "author" && filters.sort_order === "asc"
                    ? "bg-blue-600 text-white"
                    : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
                }`}
              >
                Author (A-Z)
              </button>
              <button
                onClick={() => handleSortChange("rating", "desc")}
                className={`px-3 py-1.5 rounded-lg text-sm ${
                  filters.sort_by === "rating" && filters.sort_order === "desc"
                    ? "bg-blue-600 text-white"
                    : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
                }`}
              >
                Highest Rated
              </button>
              <button
                onClick={() => handleSortChange("date_publication", "desc")}
                className={`px-3 py-1.5 rounded-lg text-sm ${
                  filters.sort_by === "date_publication" &&
                  filters.sort_order === "desc"
                    ? "bg-blue-600 text-white"
                    : "bg-white border border-gray-300 text-gray-700 hover:bg-gray-50"
                }`}
              >
                Newest First
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
