"use client";

import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import apiClient from '../utils/apiClient';
import Link from 'next/link';

interface ProgressData {
  courses_started: number;
  courses_completed: number;
  skills_acquired: string[];
  total_time_spent: number;
  certificates_earned: number;
}

export default function ProgressPage() {
  const { user } = useAuth();
  const [progress, setProgress] = useState<ProgressData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (user) {
      fetchProgress();
    }
  }, [user]);

  const fetchProgress = async () => {
    try {
      // Assuming there's an endpoint for user progress
      const response = await apiClient.get('/api/user/progress');
      setProgress(response.data);
    } catch (err) {
      // For now, use mock data
      setProgress({
        courses_started: 0,
        courses_completed: 0,
        skills_acquired: [],
        total_time_spent: 0,
        certificates_earned: 0
      });
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Please log in to view your progress</h1>
          <Link href="/auth/login" className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700">
            Login
          </Link>
        </div>
      </main>
    );
  }

  if (loading) {
    return <main className="min-h-screen flex items-center justify-center"><p>Loading progress...</p></main>;
  }

  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-indigo-600 text-white py-8">
        <div className="max-w-6xl mx-auto px-8">
          <h1 className="text-3xl font-extrabold">Your Learning Progress</h1>
          <p className="text-indigo-200">Track your achievements and growth</p>
        </div>
      </header>

      <section className="max-w-6xl mx-auto py-8 px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <h3 className="text-2xl font-bold text-indigo-600">{progress?.courses_started || 0}</h3>
            <p className="text-gray-600">Courses Started</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <h3 className="text-2xl font-bold text-green-600">{progress?.courses_completed || 0}</h3>
            <p className="text-gray-600">Courses Completed</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <h3 className="text-2xl font-bold text-purple-600">{progress?.skills_acquired?.length || 0}</h3>
            <p className="text-gray-600">Skills Acquired</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <h3 className="text-2xl font-bold text-orange-600">{progress?.certificates_earned || 0}</h3>
            <p className="text-gray-600">Certificates Earned</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-4">Skills Progress</h3>
            {progress?.skills_acquired?.length ? (
              <div className="space-y-3">
                {progress.skills_acquired.map(skill => (
                  <div key={skill}>
                    <div className="flex justify-between text-sm mb-1">
                      <span>{skill}</span>
                      <span>100%</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div className="bg-green-600 h-2 rounded-full" style={{ width: '100%' }}></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500">No skills acquired yet. Start learning to build your skills!</p>
            )}
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md">
            <h3 className="text-xl font-semibold mb-4">Recent Achievements</h3>
            {progress?.courses_completed ? (
              <ul className="space-y-2">
                {Array.from({ length: progress.courses_completed }, (_, i) => (
                  <li key={i} className="flex items-center space-x-2">
                    <span className="text-green-600">✓</span>
                    <span>Completed Course {i + 1}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">Complete courses to earn achievements!</p>
            )}
            <Link href="/certificates" className="inline-block mt-4 text-indigo-600 hover:text-indigo-800">
              View Certificates →
            </Link>
          </div>
        </div>

        <div className="text-center mt-8">
          <Link href="/learn" className="bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 transition-colors">
            Back to Dashboard
          </Link>
        </div>
      </section>
    </main>
  );
}
