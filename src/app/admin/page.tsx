"use client";

import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../utils/apiClient';
import Link from 'next/link';

interface ContentItem {
  id: string;
  title: string;
  status: string;
  created_at: string;
}

interface Analytics {
  total_users: number;
  total_content: number;
  active_users: number;
  engagement_rate: number;
}

export default function AdminDashboard() {
  const { user } = useAuth();
  const [content, setContent] = useState<ContentItem[]>([]);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      fetchData();
    }
  }, [user]);

  const fetchData = async () => {
    try {
      const [contentRes, analyticsRes] = await Promise.all([
        apiClient.get('/api/content'),
        apiClient.get('/api/admin/analytics')
      ]);
      setContent(contentRes.data);
      setAnalytics(analyticsRes.data);
    } catch (err) {
      // Mock data
      setContent([]);
      setAnalytics({
        total_users: 0,
        total_content: 0,
        active_users: 0,
        engagement_rate: 0
      });
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Admin access required</h1>
          <Link href="/auth/login" className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700">
            Login
          </Link>
        </div>
      </main>
    );
  }

  if (loading) {
    return <main className="min-h-screen flex items-center justify-center"><p>Loading admin dashboard...</p></main>;
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-red-600 text-white py-8">
        <div className="max-w-6xl mx-auto px-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-extrabold">Admin Dashboard</h1>
            <p className="text-red-200">Manage content and monitor platform</p>
          </div>
          <Link href="/" className="bg-red-700 px-4 py-2 rounded hover:bg-red-800 transition-colors">
            Back to Site
          </Link>
        </div>
      </header>

      <section className="max-w-6xl mx-auto py-8 px-8">
        {/* Analytics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <h3 className="text-2xl font-bold text-blue-600">{analytics?.total_users || 0}</h3>
            <p className="text-gray-600">Total Users</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <h3 className="text-2xl font-bold text-green-600">{analytics?.total_content || 0}</h3>
            <p className="text-gray-600">Total Content</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <h3 className="text-2xl font-bold text-purple-600">{analytics?.active_users || 0}</h3>
            <p className="text-gray-600">Active Users</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <h3 className="text-2xl font-bold text-orange-600">{analytics?.engagement_rate || 0}%</h3>
            <p className="text-gray-600">Engagement Rate</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Content Management */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold">Content Management</h3>
              <button className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition-colors">
                Add New Content
              </button>
            </div>
            {content.length === 0 ? (
              <p className="text-gray-500">No content available.</p>
            ) : (
              <ul className="space-y-2">
                {content.slice(0, 5).map(item => (
                  <li key={item.id} className="flex justify-between items-center p-2 border rounded">
                    <span>{item.title}</span>
                    <span className={`px-2 py-1 rounded text-sm ${item.status === 'approved' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>
                      {item.status}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            <Link href="/admin/content" className="inline-block mt-4 text-indigo-600 hover:text-indigo-800">
              Manage All Content →
            </Link>
          </div>

          {/* User Management */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-4">User Management</h3>
            <p className="text-gray-600 mb-4">Monitor user activity and engagement.</p>
            <Link href="/admin/users" className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 transition-colors">
              View Users
            </Link>
          </div>
        </div>

        <div className="text-center mt-8">
          <Link href="/admin/reports" className="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 transition-colors">
            Generate Reports
          </Link>
        </div>
      </section>
    </main>
  );
}
