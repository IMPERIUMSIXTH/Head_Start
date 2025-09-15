"use client";

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '../utils/apiClient';

export default function OnboardingPage() {
  const router = useRouter();

  const [interests, setInterests] = useState<string[]>([]);
  const [goals, setGoals] = useState('');
  const [skillLevel, setSkillLevel] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const interestOptions = [
    'Programming', 'Data Science', 'Machine Learning', 'Web Development',
    'Mobile Development', 'DevOps', 'Cybersecurity', 'Cloud Computing',
    'AI Ethics', 'Business Analysis', 'Project Management', 'Design'
  ];

  const handleInterestChange = (interest: string) => {
    setInterests(prev =>
      prev.includes(interest)
        ? prev.filter(i => i !== interest)
        : [...prev, interest]
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await apiClient.post('/api/user/preferences', {
        interests,
        goals,
        skill_level: skillLevel
      });
      router.push('/learn');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save preferences');
    } finally {
      setLoading(false);
    }
  };

  // New state for tutorial step
  const [tutorialStep, setTutorialStep] = useState(0);

  // Tutorial steps content
  const tutorialSteps = [
    "Select your interests to personalize your learning.",
    "Set your learning goals to stay focused.",
    "Choose your current skill level.",
    "Complete onboarding to get tailored recommendations!"
  ];

  // Function to go to next tutorial step
  const nextStep = () => {
    if (tutorialStep < tutorialSteps.length - 1) {
      setTutorialStep(tutorialStep + 1);
    }
  };

  // Function to go to previous tutorial step
  const prevStep = () => {
    if (tutorialStep > 0) {
      setTutorialStep(tutorialStep - 1);
    }
  };

  return (
    <main className="min-h-screen bg-gradient-to-r from-blue-50 to-indigo-100 p-6">
      <div className="max-w-2xl mx-auto bg-white p-8 rounded-lg shadow-md">
        <h1 className="text-3xl font-bold mb-6 text-center text-indigo-900">Tell us about yourself</h1>
        <p className="text-gray-600 mb-8 text-center">Help us personalize your learning experience</p>
        {error && <p className="text-red-600 mb-4">{error}</p>}

        {/* Tutorial box */}
        <div className="mb-6 p-4 bg-indigo-100 rounded-lg text-indigo-900 font-semibold text-center">
          {tutorialSteps[tutorialStep]}
          <div className="mt-2 flex justify-center space-x-4">
            <button
              onClick={prevStep}
              disabled={tutorialStep === 0}
              className="px-3 py-1 bg-indigo-300 rounded disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={nextStep}
              disabled={tutorialStep === tutorialSteps.length - 1}
              className="px-3 py-1 bg-indigo-600 text-white rounded disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-indigo-700 font-semibold mb-3">What are your interests? (Select all that apply)</label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {interestOptions.map(interest => (
                <label key={interest} className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={interests.includes(interest)}
                    onChange={() => handleInterestChange(interest)}
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="text-sm">{interest}</span>
                </label>
              ))}
            </div>
          </div>
          <div>
            <label htmlFor="goals" className="block text-indigo-700 font-semibold mb-2">What are your learning goals?</label>
            <textarea
              id="goals"
              value={goals}
              onChange={(e) => setGoals(e.target.value)}
              placeholder="e.g., Become a full-stack developer, Learn data analysis, etc."
              rows={3}
              className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
          <div>
            <label htmlFor="skillLevel" className="block text-indigo-700 font-semibold mb-2">What's your current skill level?</label>
            <select
              id="skillLevel"
              value={skillLevel}
              onChange={(e) => setSkillLevel(e.target.value)}
              className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <option value="">Select your skill level</option>
              <option value="beginner">Beginner - New to the field</option>
              <option value="intermediate">Intermediate - Some experience</option>
              <option value="advanced">Advanced - Experienced professional</option>
            </select>
          </div>
          <button
            type="submit"
            disabled={loading || interests.length === 0 || !goals || !skillLevel}
            className="w-full bg-indigo-700 text-white py-3 rounded hover:bg-indigo-800 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Saving preferences...' : 'Complete Onboarding'}
          </button>
        </form>
      </div>
    </main>
  );
}
