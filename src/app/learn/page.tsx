"use client";

import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../utils/apiClient';
import Link from 'next/link';

interface Recommendation {
  content_id: string;
  title: string;
  description?: string;
  content_type: string;
  source: string;
  url?: string;
  duration_minutes?: number;
  difficulty_level?: string;
  topics: string[];
  language: string;
  recommendation_score: number;
  explanation_factors: any;
  created_at: string;
}

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      fetchRecommendations();
    }
  }, [user]);

  const fetchRecommendations = async () => {
    try {
      const response = await apiClient.get('/api/recommendations/feed');
      setRecommendations(response.data.recommendations);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load recommendations');
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Please log in to access your dashboard</h1>
          <Link href="/auth/login" className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700">
            Login
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-indigo-600 text-white py-8">
        <div className="max-w-6xl mx-auto px-8 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-extrabold">Welcome back, {user.username}!</h1>
            <p className="text-indigo-200">Your personalized learning dashboard</p>
          </div>
          <button
            onClick={logout}
            className="bg-indigo-700 px-4 py-2 rounded hover:bg-indigo-800 transition-colors"
          >
            Logout
          </button>
        </div>
      </header>

      <section className="max-w-6xl mx-auto py-8 px-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Recommendations */}
          <div className="lg:col-span-2">
            <h2 className="text-2xl font-bold mb-6 text-gray-800">Recommended for You</h2>
            {loading ? (
              <p>Loading recommendations...</p>
            ) : error ? (
              <p className="text-red-600">{error}</p>
            ) : recommendations.length === 0 ? (
              <p>No recommendations available yet. Complete your onboarding to get personalized suggestions!</p>
            ) : (
              <div className="space-y-4">
                {recommendations.map((rec) => (
                  <div
                    key={rec.content_id}
                    className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow transform hover:scale-105 hover:z-10"
                    style={{ transition: 'transform 0.3s ease' }}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-xl font-semibold text-gray-800">{rec.title}</h3>
                      <span className="bg-indigo-100 text-indigo-800 px-2 py-1 rounded text-sm">
                        {rec.recommendation_score.toFixed(2)} relevance
                      </span>
                    </div>
                    <p className="text-gray-600 mb-3">{rec.description}</p>
                    <div className="flex flex-wrap gap-2 mb-3">
                      {rec.topics.map(topic => (
                        <span key={topic} className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-sm">
                          {topic}
                        </span>
                      ))}
                    </div>
                    <div className="flex justify-between items-center text-sm text-gray-500">
                      <span>{rec.content_type} • {rec.source}</span>
                      {rec.duration_minutes && <span>{rec.duration_minutes} min</span>}
                    </div>
                    {rec.url && (
                      <a
                        href={rec.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-block mt-3 bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 transition-colors"
                      >
                        Start Learning
                      </a>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Progress Summary */}
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">Your Progress</h3>
              <div className="space-y-3">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Courses Started</span>
                    <span>0</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-indigo-600 h-2 rounded-full" style={{ width: '0%' }}></div>
                  </div>
                </div>
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Skills Acquired</span>
                    <span>0</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div className="bg-indigo-600 h-2 rounded-full" style={{ width: '0%' }}></div>
                  </div>
                </div>
              </div>
              <Link href="/progress" className="inline-block mt-4 text-indigo-600 hover:text-indigo-800">
                View detailed progress →
              </Link>
            </div>

            {/* Quick Actions */}
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h3 className="text-lg font-semibold mb-4 text-gray-800">Quick Actions</h3>
              <div className="space-y-2">
                <Link href="/recommendations" className="block bg-indigo-50 text-indigo-700 px-4 py-2 rounded hover:bg-indigo-100">
                  View All Recommendations
                </Link>
                <Link href="/onboarding" className="block bg-green-50 text-green-700 px-4 py-2 rounded hover:bg-green-100">
                  Update Preferences
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
