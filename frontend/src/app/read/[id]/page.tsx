"use client";

import { useState, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import {
  Settings,
  Sun,
  Moon,
  Type,
  ArrowLeft,
  BookOpen,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { booksApi } from "@/lib/api/books";
import { readingProgressApi } from "@/lib/api/reading-progress";
import { Book, BookContent } from "@/types/api";

type Theme = "light" | "dark";
type FontSize = "small" | "medium" | "large";

const fontSizeMap = {
  small: "text-base",
  medium: "text-lg",
  large: "text-xl",
};

export default function ReadingPage() {
  const params = useParams();
  const router = useRouter();
  const { data: session } = useSession();
  const bookId = parseInt(params.id as string);
  const contentRef = useRef<HTMLDivElement>(null);

  const [book, setBook] = useState<Book | null>(null);
  const [bookContent, setBookContent] = useState<BookContent | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingPage, setIsLoadingPage] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [theme, setTheme] = useState<Theme>("light");
  const [fontSize, setFontSize] = useState<FontSize>("medium");
  const [currentPage, setCurrentPage] = useState(1);
  const [pageInput, setPageInput] = useState("1");

  useEffect(() => {
    loadBook();
    if (session?.accessToken) {
      loadReadingProgress();
    } else {
      loadContent(1);
    }
  }, [bookId, session]);

  useEffect(() => {
    // Save progress when page changes
    if (session?.accessToken && currentPage > 0) {
      const timeoutId = setTimeout(() => {
        saveProgress();
      }, 2000); // Debounce save by 2 seconds

      return () => clearTimeout(timeoutId);
    }
  }, [currentPage, session]);

  const loadBook = async () => {
    try {
      const data = await booksApi.getBook(bookId, session?.accessToken);
      setBook(data);
    } catch (error) {
      console.error("Failed to load book:", error);
    }
  };

  const loadContent = async (page: number) => {
    setIsLoadingPage(true);
    try {
      const content = await booksApi.getBookContent(
        bookId,
        page,
        300,
        session?.accessToken
      );
      setBookContent(content);
      setCurrentPage(page);
      setPageInput(page.toString());
      
      // Scroll to top when loading new page
      if (contentRef.current) {
        contentRef.current.scrollTop = 0;
      }
    } catch (error) {
      console.error("Failed to load content:", error);
    } finally {
      setIsLoadingPage(false);
      setIsLoading(false);
    }
  };

  const loadReadingProgress = async () => {
    if (!session?.accessToken) return;

    try {
      const progress = await readingProgressApi.getProgress(
        bookId,
        session.accessToken
      );

      if (progress && progress.current_page) {
        // Load the saved page
        loadContent(progress.current_page);
      } else {
        // Load first page if no progress
        loadContent(1);
      }
    } catch (error) {
      console.error("Failed to load reading progress:", error);
      // Load first page on error
      loadContent(1);
    }
  };

  const saveProgress = async () => {
    if (!session?.accessToken || !currentPage) return;

    try {
      await readingProgressApi.updateProgress(
        bookId,
        { current_page: currentPage },
        session.accessToken
      );
    } catch (error) {
      console.error("Failed to save progress:", error);
    }
  };

  const goToNextPage = () => {
    if (bookContent?.has_next) {
      loadContent(currentPage + 1);
    }
  };

  const goToPreviousPage = () => {
    if (bookContent?.has_previous) {
      loadContent(currentPage - 1);
    }
  };

  const goToPage = (page: number) => {
    if (page >= 1 && page <= (bookContent?.total_pages || 1)) {
      loadContent(page);
    }
  };

  const handlePageInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPageInput(e.target.value);
  };

  const handlePageInputSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const page = parseInt(pageInput);
    if (!isNaN(page)) {
      goToPage(page);
    }
  };

  const handleClose = async () => {
    if (session?.accessToken) {
      await saveProgress();
    }
    router.push(`/books/${bookId}`);
  };

  const themeClasses = {
    light: "bg-white text-gray-900",
    dark: "bg-gray-900 text-gray-100",
  };

  if (isLoading) {
    return (
      <div className="h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <BookOpen className="h-12 w-12 text-blue-600 mx-auto mb-4 animate-pulse" />
          <p className="text-gray-600">Loading book...</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`h-screen flex flex-col ${themeClasses[theme]}`}>
      {/* Header */}
      <div
        className={`flex items-center justify-between px-6 py-4 border-b ${
          theme === "dark" ? "border-gray-700" : "border-gray-200"
        }`}
      >
        <div className="flex items-center gap-4">
          <button
            onClick={handleClose}
            className="p-2 rounded-lg hover:bg-blue-600 hover:text-white dark:hover:bg-blue-600 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="font-semibold">{book?.titre}</h1>
            <p className="text-sm opacity-70">{book?.auteur}</p>
          </div>
        </div>

        <div className="flex items-center gap-4">
          {/* Page Navigation */}
          <div className="flex items-center gap-2">
            <button
              onClick={goToPreviousPage}
              disabled={!bookContent?.has_previous || isLoadingPage}
              className="p-2 rounded-lg hover:bg-blue-600 hover:text-white dark:hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            
            <div className="flex items-center gap-2">
              <form onSubmit={handlePageInputSubmit} className="flex items-center gap-2">
                <span className="text-sm">Page</span>
                <input
                  type="number"
                  value={pageInput}
                  onChange={handlePageInputChange}
                  className="w-16 px-2 py-1 text-sm text-center text-white bg-blue-600 border-2 border-blue-600 rounded font-semibold focus:ring-2 focus:ring-blue-400 focus:border-blue-400 dark:bg-blue-600 dark:text-white dark:border-blue-600 dark:focus:ring-blue-400 dark:focus:border-blue-400 transition-colors"
                  min="1"
                  max={bookContent?.total_pages || 1}
                />
                <span className="text-sm opacity-70">
                  of {bookContent?.total_pages || "?"}
                </span>
              </form>
              {bookContent && (
                <span className="text-xs font-semibold text-blue-600 ml-2">
                  ({((currentPage / bookContent.total_pages) * 100).toFixed(1)}%)
                </span>
              )}
            </div>

            <button
              onClick={goToNextPage}
              disabled={!bookContent?.has_next || isLoadingPage}
              className="p-2 rounded-lg hover:bg-blue-600 hover:text-white dark:hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>

          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 rounded-lg hover:bg-blue-600 hover:text-white dark:hover:bg-blue-600 transition-colors"
          >
            <Settings className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="h-1 bg-gray-200 dark:bg-gray-700">
        <div
          className="h-full bg-blue-600 transition-all duration-300"
          style={{ 
            width: `${bookContent ? ((currentPage / bookContent.total_pages) * 100).toFixed(1) : 0}%` 
          }}
        />
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div
          className={`absolute top-16 right-6 p-4 rounded-lg shadow-lg border z-10 ${
            theme === "dark"
              ? "bg-gray-800 border-gray-700"
              : "bg-white border-gray-200"
          }`}
        >
          <h3 className="font-semibold mb-4">Reading Settings</h3>

          <div className="space-y-4">
            {/* Theme Toggle */}
            <div>
              <label className="block text-sm font-medium mb-2">Theme</label>
              <div className="flex gap-2">
                <button
                  onClick={() => setTheme("light")}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
                    theme === "light"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 dark:bg-gray-700"
                  }`}
                >
                  <Sun className="h-4 w-4" />
                  Light
                </button>
                <button
                  onClick={() => setTheme("dark")}
                  className={`flex items-center gap-2 px-3 py-2 rounded-lg ${
                    theme === "dark"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 dark:bg-gray-700"
                  }`}
                >
                  <Moon className="h-4 w-4" />
                  Dark
                </button>
              </div>
            </div>

            {/* Font Size */}
            <div>
              <label className="block text-sm font-medium mb-2">
                Font Size
              </label>
              <div className="flex gap-2">
                <button
                  onClick={() => setFontSize("small")}
                  className={`px-3 py-2 rounded-lg ${
                    fontSize === "small"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 dark:bg-gray-700"
                  }`}
                >
                  <Type className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setFontSize("medium")}
                  className={`px-3 py-2 rounded-lg ${
                    fontSize === "medium"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 dark:bg-gray-700"
                  }`}
                >
                  <Type className="h-5 w-5" />
                </button>
                <button
                  onClick={() => setFontSize("large")}
                  className={`px-3 py-2 rounded-lg ${
                    fontSize === "large"
                      ? "bg-blue-600 text-white"
                      : "bg-gray-100 dark:bg-gray-700"
                  }`}
                >
                  <Type className="h-6 w-6" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Content */}
      <div
        ref={contentRef}
        className="flex-1 overflow-y-auto px-6 py-8"
      >
        <div className="max-w-3xl mx-auto">
          {isLoadingPage ? (
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <BookOpen className="h-8 w-8 text-blue-600 mx-auto mb-2 animate-pulse" />
                <p className="text-sm opacity-70">Loading page...</p>
              </div>
            </div>
          ) : (
            <div className={`${fontSizeMap[fontSize]} leading-relaxed whitespace-pre-wrap`}>
              {bookContent?.content || "No content available"}
            </div>
          )}
        </div>

        {/* Page Navigation Footer */}
        {bookContent && !isLoadingPage && (
          <div className="max-w-3xl mx-auto mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between">
              <button
                onClick={goToPreviousPage}
                disabled={!bookContent.has_previous}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-300 disabled:text-gray-500"
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </button>

              <div className="flex flex-col items-center">
                <span className="text-sm opacity-70">
                  Page {currentPage} of {bookContent.total_pages}
                </span>
                <span className="text-xs font-semibold text-blue-600">
                  {((currentPage / bookContent.total_pages) * 100).toFixed(1)}% Complete
                </span>
              </div>

              <button
                onClick={goToNextPage}
                disabled={!bookContent.has_next}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-300 disabled:text-gray-500"
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
