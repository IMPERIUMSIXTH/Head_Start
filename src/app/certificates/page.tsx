"use client";

import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import Link from 'next/link';

interface Certificate {
  id: string;
  title: string;
  issued_date: string;
  course_title: string;
}

export default function CertificatesPage() {
  const { user } = useAuth();
  const [certificates, setCertificates] = useState<Certificate[]>([]);

  useEffect(() => {
    if (user) {
      // Mock data for now
      setCertificates([]);
    }
  }, [user]);

  if (!user) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <h1 className="text-2xl font-bold mb-4">Please log in to view certificates</h1>
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
        <div className="max-w-6xl mx-auto px-8">
          <h1 className="text-3xl font-extrabold">Your Certificates</h1>
          <p className="text-indigo-200">Showcase your learning achievements</p>
        </div>
      </header>

      <section className="max-w-6xl mx-auto py-8 px-8">
        {certificates.length === 0 ? (
          <div className="text-center">
            <h2 className="text-2xl font-semibold mb-4">No certificates yet</h2>
            <p className="text-gray-600 mb-6">Complete courses to earn certificates!</p>
            <Link href="/learn" className="bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 transition-colors">
              Start Learning
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {certificates.map(cert => (
              <div key={cert.id} className="bg-white p-6 rounded-lg shadow-md border-l-4 border-indigo-600">
                <h3 className="text-xl font-semibold mb-2">{cert.title}</h3>
                <p className="text-gray-600 mb-2">Course: {cert.course_title}</p>
                <p className="text-sm text-gray-500">Issued: {new Date(cert.issued_date).toLocaleDateString()}</p>
                <button className="mt-4 bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 transition-colors">
                  Download PDF
                </button>
              </div>
            ))}
          </div>
        )}

        <div className="text-center mt-8">
          <Link href="/progress" className="text-indigo-600 hover:text-indigo-800">
            ← Back to Progress
          </Link>
        </div>
      </section>
    </main>
  );
}
