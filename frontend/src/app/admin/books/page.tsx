'use client';

import { useEffect, useState } from 'react';
import { booksApi } from '@/lib/api/books';
import { deleteBook } from '@/lib/api/admin';
import Link from 'next/link';

export default function AdminBooksPage() {
  const [books, setBooks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [importing, setImporting] = useState(false);

  const fetchBooks = async () => {
    setLoading(true);
    try {
      const data = await booksApi.getBooks(page, 20, {
        search: search || undefined,
      });
      setBooks(data.items);
      setTotalPages(data.total_pages);
    } catch (error) {
      console.error('Failed to fetch books:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBooks();
  }, [page]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchBooks();
  };

  const handleDelete = async (bookId: number, title: string) => {
    if (!confirm(`Are you sure you want to delete "${title}"? This action cannot be undone.`)) return;
    
    try {
      await deleteBook(bookId);
      fetchBooks();
    } catch (error) {
      alert('Failed to delete book');
    }
  };

  const exportToCSV = () => {
    const csvContent = [
      ['ID', 'Title', 'ISBN', 'Authors', 'Genres', 'Rating', 'Reviews', 'Pages', 'Language'].join(','),
      ...books.map(book => [
        book.id,
        `"${book.titre}"`,
        book.isbn || '',
        `"${book.author_names?.join('; ') || ''}"`,
        `"${book.genre_names?.join('; ') || ''}"`,
        book.average_rating?.toFixed(2) || '0.00',
        book.review_count || 0,
        book.nombre_pages || 0,
        book.langue || ''
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `books_export_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handleImportCSV = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setImporting(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/v1/admin/books/import', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Import failed');

      const result = await response.json();
      alert(`Successfully imported ${result.imported_count} books`);
      fetchBooks();
    } catch (error) {
      alert('Failed to import books');
    } finally {
      setImporting(false);
      e.target.value = '';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Book Management</h1>
          <p className="mt-2 text-gray-900">Manage book collection</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={exportToCSV}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
          >
            <span>📥</span>
            Export CSV
          </button>
          <label className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 cursor-pointer flex items-center gap-2">
            <span>📤</span>
            {importing ? 'Importing...' : 'Import CSV'}
            <input
              type="file"
              accept=".csv"
              onChange={handleImportCSV}
              className="hidden"
              disabled={importing}
            />
          </label>
        </div>
      </div>

      {/* Search */}
      <div className="bg-white rounded-lg shadow p-6">
        <form onSubmit={handleSearch} className="flex gap-4">
          <input
            type="text"
            placeholder="Search books by title or author..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 placeholder-gray-500"
          />
          <button
            type="submit"
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Search
          </button>
        </form>
      </div>

      {/* Books Table */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Book</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Authors</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Genres</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Rating</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Reviews</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {books.map((book) => (
                <tr key={book.id}>
                  <td className="px-6 py-4">
                    <div className="font-medium text-gray-900">{book.titre}</div>
                    {book.isbn && (
                      <div className="text-sm text-gray-900">ISBN: {book.isbn}</div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {book.author_names?.join(', ') || 'Unknown'}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-900">
                    {book.genre_names?.join(', ') || 'None'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <span className="text-yellow-500">⭐</span>
                      <span className="ml-1 text-sm font-medium text-gray-900">
                        {book.average_rating?.toFixed(1) || '0.0'}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {book.review_count || 0}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end gap-2">
                      <Link
                        href={`/books/${book.id}`}
                        className="text-blue-600 hover:text-blue-900"
                      >
                        View
                      </Link>
                      <button
                        onClick={() => handleDelete(book.id, book.titre)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
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
