
"use client";

import Link from 'next/link';

const InteractiveDashboard = () => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
      <div className="flip-card">
        <div className="flip-card-inner">
          <div className="flip-card-front bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold text-indigo-800 mb-2">Dashboard &rarr;</h2>
            <p className="text-indigo-600">Access your personalized learning dashboard.</p>
          </div>
          <div className="flip-card-back bg-indigo-800 p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold text-white mb-2">Dashboard</h2>
            <p className="text-indigo-200">View your progress, get recommendations, and continue your learning journey.</p>
            <Link href="/learn" className="mt-4 inline-block bg-white text-indigo-800 px-4 py-2 rounded-full">
              Go to Dashboard
            </Link>
          </div>
        </div>
      </div>
      <div className="flip-card">
        <div className="flip-card-inner">
          <div className="flip-card-front bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold text-indigo-800 mb-2">Progress &rarr;</h2>
            <p className="text-indigo-600">Track your learning progress and achievements.</p>
          </div>
          <div className="flip-card-back bg-indigo-800 p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold text-white mb-2">Progress</h2>
            <p className="text-indigo-200">Visualize your growth, see completed courses, and identify areas for improvement.</p>
            <Link href="/progress" className="mt-4 inline-block bg-white text-indigo-800 px-4 py-2 rounded-full">
              View Progress
            </Link>
          </div>
        </div>
      </div>
      <div className="flip-card">
        <div className="flip-card-inner">
          <div className="flip-card-front bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold text-indigo-800 mb-2">Recommendations &rarr;</h2>
            <p className="text-indigo-600">View AI-generated personalized recommendations.</p>
          </div>
          <div className="flip-card-back bg-indigo-800 p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold text-white mb-2">Recommendations</h2>
            <p className="text-indigo-200">Discover new courses and content tailored to your interests and goals.</p>
            <Link href="/recommendations" className="mt-4 inline-block bg-white text-indigo-800 px-4 py-2 rounded-full">
              Get Recommendations
            </Link>
          </div>
        </div>
      </div>
      <div className="flip-card">
        <div className="flip-card-inner">
          <div className="flip-card-front bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold text-indigo-800 mb-2">Docs &rarr;</h2>
            <p className="text-indigo-600">Find in-depth information about HeadStart features and API.</p>
          </div>
          <div className="flip-card-back bg-indigo-800 p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold text-white mb-2">Documentation</h2>
            <p className="text-indigo-200">Explore our comprehensive documentation to get the most out of HeadStart.</p>
            <Link href="/docs" className="mt-4 inline-block bg-white text-indigo-800 px-4 py-2 rounded-full">
              Read Docs
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InteractiveDashboard;
