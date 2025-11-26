'use client';

import { useEffect, useState } from 'react';
import { getUsers, suspendUser, activateUser, deleteUser, promoteToAdmin, revokeAdmin } from '@/lib/api/admin';

export default function AdminUsersPage() {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState('');
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined);
  const [importing, setImporting] = useState(false);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await getUsers({
        page,
        page_size: 20,
        search: search || undefined,
        is_active: filterActive,
      });
      setUsers(data.users);
      setTotalPages(data.total_pages);
    } catch (error) {
      console.error('Failed to fetch users:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, [page, filterActive]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchUsers();
  };

  const handleSuspend = async (userId: number) => {
    if (!confirm('Are you sure you want to suspend this user?')) return;
    
    try {
      await suspendUser(userId);
      fetchUsers();
    } catch (error) {
      alert('Failed to suspend user');
    }
  };

  const handleActivate = async (userId: number) => {
    try {
      await activateUser(userId);
      fetchUsers();
    } catch (error) {
      alert('Failed to activate user');
    }
  };

  const handleDelete = async (userId: number) => {
    if (!confirm('Are you sure you want to permanently delete this user? This action cannot be undone.')) return;
    
    try {
      await deleteUser(userId);
      fetchUsers();
    } catch (error) {
      alert('Failed to delete user');
    }
  };

  const handlePromote = async (userId: number) => {
    if (!confirm('Are you sure you want to promote this user to admin?')) return;
    
    try {
      await promoteToAdmin(userId);
      fetchUsers();
    } catch (error) {
      alert('Failed to promote user');
    }
  };

  const handleRevoke = async (userId: number) => {
    if (!confirm('Are you sure you want to revoke admin privileges from this user?')) return;
    
    try {
      await revokeAdmin(userId);
      fetchUsers();
    } catch (error) {
      alert('Failed to revoke admin');
    }
  };

  const exportToCSV = () => {
    const csvContent = [
      ['ID', 'Name', 'Email', 'Status', 'Role', 'Reviews', 'Favorites', 'Created At'].join(','),
      ...users.map(user => [
        user.id,
        `"${user.full_name}"`,
        user.email,
        user.is_active ? 'Active' : 'Suspended',
        user.is_admin ? 'Admin' : 'User',
        user.reviews_count,
        user.favorites_count,
        new Date(user.created_at).toISOString()
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `users_export_${new Date().toISOString().split('T')[0]}.csv`;
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
      const response = await fetch('http://localhost:8000/api/v1/admin/users/import', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Import failed');

      const result = await response.json();
      alert(`Successfully imported ${result.imported_count} users`);
      fetchUsers();
    } catch (error) {
      alert('Failed to import users');
    } finally {
      setImporting(false);
      e.target.value = '';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">User Management</h1>
          <p className="mt-2 text-gray-900">Manage user accounts and permissions</p>
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

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6">
        <form onSubmit={handleSearch} className="flex gap-4">
          <input
            type="text"
            placeholder="Search by name or email..."
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

        <div className="mt-4 flex gap-4">
          <button
            onClick={() => setFilterActive(undefined)}
            className={`px-4 py-2 rounded-lg border-2 font-medium transition-colors ${
              filterActive === undefined 
                ? 'bg-blue-600 text-white border-blue-600' 
                : 'bg-white text-gray-900 border-gray-300 hover:border-blue-400'
            }`}
          >
            All Users
          </button>
          <button
            onClick={() => setFilterActive(true)}
            className={`px-4 py-2 rounded-lg border-2 font-medium transition-colors ${
              filterActive === true 
                ? 'bg-green-600 text-white border-green-600' 
                : 'bg-white text-gray-900 border-gray-300 hover:border-green-400'
            }`}
          >
            Active
          </button>
          <button
            onClick={() => setFilterActive(false)}
            className={`px-4 py-2 rounded-lg border-2 font-medium transition-colors ${
              filterActive === false 
                ? 'bg-red-600 text-white border-red-600' 
                : 'bg-white text-gray-900 border-gray-300 hover:border-red-400'
            }`}
          >
            Suspended
          </button>
        </div>
      </div>

      {/* Users Table */}
      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">User</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Role</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-700 uppercase">Stats</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-700 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {users.map((user) => (
                <tr key={user.id}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-medium text-gray-900">{user.full_name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {user.email}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {user.is_active ? 'Active' : 'Suspended'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      user.is_admin ? 'bg-purple-100 text-purple-800' : 'bg-gray-100 text-gray-900'
                    }`}>
                      {user.is_admin ? 'Admin' : 'User'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div>{user.reviews_count} reviews</div>
                    <div>{user.favorites_count} favorites</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end gap-2">
                      {user.is_active ? (
                        <button
                          onClick={() => handleSuspend(user.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Suspend
                        </button>
                      ) : (
                        <button
                          onClick={() => handleActivate(user.id)}
                          className="text-green-600 hover:text-green-900"
                        >
                          Activate
                        </button>
                      )}
                      
                      {user.is_admin ? (
                        <button
                          onClick={() => handleRevoke(user.id)}
                          className="text-orange-600 hover:text-orange-900"
                        >
                          Revoke Admin
                        </button>
                      ) : (
                        <button
                          onClick={() => handlePromote(user.id)}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Make Admin
                        </button>
                      )}
                      
                      <button
                        onClick={() => handleDelete(user.id)}
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
