'use client';

import { useEffect, useState } from 'react';
import { getOverviewAnalytics, getUserAnalytics, getBookAnalytics, getReviewAnalytics } from '@/lib/api/admin';

export default function AdminDashboard() {
  const [overview, setOverview] = useState<any>(null);
  const [userStats, setUserStats] = useState<any>(null);
  const [bookStats, setBookStats] = useState<any>(null);
  const [reviewStats, setReviewStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const [overviewData, userData, bookData, reviewData] = await Promise.all([
          getOverviewAnalytics(),
          getUserAnalytics(),
          getBookAnalytics(),
          getReviewAnalytics(),
        ]);

        setOverview(overviewData);
        setUserStats(userData);
        setBookStats(bookData);
        setReviewStats(reviewData);
      } catch (error) {
        console.error('Failed to fetch analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard Overview</h1>
        <p className="mt-2 text-gray-600">System statistics and analytics</p>
      </div>

      {/* Overview Stats */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Books"
            value={overview.total_books}
            icon="📚"
            color="blue"
          />
          <StatCard
            title="Total Users"
            value={overview.total_users}
            subtitle={`${overview.total_active_users} active`}
            icon="👥"
            color="green"
          />
          <StatCard
            title="Total Reviews"
            value={overview.total_reviews}
            subtitle={`${overview.new_reviews_this_week} this week`}
            icon="⭐"
            color="yellow"
          />
          <StatCard
            title="Active Readers"
            value={overview.active_readers}
            subtitle={`${overview.total_reading_sessions} sessions`}
            icon="📖"
            color="purple"
          />
        </div>
      )}

      {/* Recent Activity */}
      {overview && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm text-gray-600">New Users (7 days)</p>
              <p className="text-2xl font-bold text-blue-600">{overview.new_users_this_week}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">New Reviews (7 days)</p>
              <p className="text-2xl font-bold text-green-600">{overview.new_reviews_this_week}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Average Rating</p>
              <p className="text-2xl font-bold text-yellow-600">{overview.average_book_rating.toFixed(1)} ⭐</p>
            </div>
          </div>
        </div>
      )}

      {/* Top Books */}
      {bookStats && bookStats.most_reviewed_books && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Most Reviewed Books</h2>
          <div className="space-y-3">
            {bookStats.most_reviewed_books.slice(0, 5).map((book: any) => (
              <div key={book.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div>
                  <p className="font-medium">{book.title}</p>
                  <p className="text-sm text-gray-600">{book.review_count} reviews</p>
                </div>
                <div className="text-right">
                  <p className="text-lg font-semibold text-yellow-600">
                    {book.average_rating.toFixed(1)} ⭐
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rating Distribution */}
      {reviewStats && reviewStats.rating_distribution && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Rating Distribution</h2>
          <div className="space-y-3">
            {reviewStats.rating_distribution.map((item: any) => (
              <div key={item.rating} className="flex items-center">
                <span className="w-16 text-sm font-medium">{item.rating} ⭐</span>
                <div className="flex-1 bg-gray-200 rounded-full h-6 mx-4">
                  <div
                    className="bg-yellow-500 h-6 rounded-full flex items-center justify-end px-2"
                    style={{
                      width: `${(item.count / Math.max(...reviewStats.rating_distribution.map((r: any) => r.count))) * 100}%`,
                    }}
                  >
                    <span className="text-xs font-medium text-white">{item.count}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  title,
  value,
  subtitle,
  icon,
  color,
}: {
  title: string;
  value: number;
  subtitle?: string;
  icon: string;
  color: string;
}) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    green: 'bg-green-50 text-green-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    purple: 'bg-purple-50 text-purple-600',
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-3xl font-bold mt-2">{value.toLocaleString()}</p>
          {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`text-4xl ${colorClasses[color as keyof typeof colorClasses]} p-3 rounded-lg`}>
          {icon}
        </div>
      </div>
    </div>
  );
}
