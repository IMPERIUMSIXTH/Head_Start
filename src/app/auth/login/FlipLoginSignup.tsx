"use client";

import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useRouter } from 'next/navigation';
import '../flip-card.css';

export default function FlipLoginSignup() {
  const [flipped, setFlipped] = useState(false);
  const [loginData, setLoginData] = useState({ email: '', password: '' });
  const [signupData, setSignupData] = useState({ email: '', password: '', confirmPassword: '', fullName: '' });
  const { login, signup, loading, error } = useAuth();
  const router = useRouter();

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    await login(loginData.email, loginData.password);
    router.push('/learn');
  };

  const handleSignupSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (signupData.password !== signupData.confirmPassword) {
      // For now, just alert, later use error state
      alert('Passwords do not match');
      return;
    }
    await signup(signupData.email, signupData.password, signupData.fullName);
    router.push('/learn');
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>, form: 'login' | 'signup') => {
    const { name, value } = e.target;
    if (form === 'login') {
      setLoginData(prev => ({ ...prev, [name]: value }));
    } else {
      setSignupData(prev => ({ ...prev, [name]: value }));
    }
  };

  return (
    <div className={`flip-card-container ${flipped ? 'flipped' : ''}`}>
      <div className="flip-card">
        {/* Front Side - Login */}
        <div className="flip-card-front p-8 bg-white rounded-lg shadow-lg">
          <h2 className="text-2xl font-bold mb-6">Login</h2>
          <form onSubmit={handleLoginSubmit}>
            <label className="block mb-2 font-semibold" htmlFor="email">Email</label>
            <input
              id="email"
              name="email"
              type="email"
              value={loginData.email}
              onChange={(e) => handleInputChange(e, 'login')}
              className="w-full mb-4 p-2 border rounded"
              required
            />
            <label className="block mb-2 font-semibold" htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              value={loginData.password}
              onChange={(e) => handleInputChange(e, 'login')}
              className="w-full mb-4 p-2 border rounded"
              required
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 transition-colors"
            >
              {loading ? 'Logging in...' : 'Login'}
            </button>
            {error && <p className="text-red-600 mt-2">{error}</p>}
          </form>
          <p className="mt-4 text-center">
            Don't have an account?{' '}
            <button
              onClick={() => setFlipped(true)}
              className="text-indigo-600 hover:underline"
              type="button"
            >
              Sign Up
            </button>
          </p>
        </div>

        {/* Back Side - Signup */}
        <div className="flip-card-back p-8 bg-white rounded-lg shadow-lg">
          <h2 className="text-2xl font-bold mb-6">Sign Up</h2>
          <form onSubmit={handleSignupSubmit}>
            <label className="block mb-2 font-semibold" htmlFor="fullName">Full Name</label>
            <input
              id="fullName"
              name="fullName"
              type="text"
              value={signupData.fullName}
              onChange={(e) => handleInputChange(e, 'signup')}
              className="w-full mb-4 p-2 border rounded"
              required
            />
            <label className="block mb-2 font-semibold" htmlFor="signup-email">Email</label>
            <input
              id="signup-email"
              name="email"
              type="email"
              value={signupData.email}
              onChange={(e) => handleInputChange(e, 'signup')}
              className="w-full mb-4 p-2 border rounded"
              required
            />
            <label className="block mb-2 font-semibold" htmlFor="signup-password">Password</label>
            <input
              id="signup-password"
              name="password"
              type="password"
              value={signupData.password}
              onChange={(e) => handleInputChange(e, 'signup')}
              className="w-full mb-4 p-2 border rounded"
              required
            />
            <label className="block mb-2 font-semibold" htmlFor="signup-confirm-password">Confirm Password</label>
            <input
              id="signup-confirm-password"
              name="confirmPassword"
              type="password"
              value={signupData.confirmPassword}
              onChange={(e) => handleInputChange(e, 'signup')}
              className="w-full mb-4 p-2 border rounded"
              required
            />
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 transition-colors"
            >
              {loading ? 'Signing up...' : 'Sign Up'}
            </button>
            {error && <p className="text-red-600 mt-2">{error}</p>}
          </form>
          <p className="mt-4 text-center">
            Already have an account?{' '}
            <button
              onClick={() => setFlipped(false)}
              className="text-indigo-600 hover:underline"
              type="button"
            >
              Login
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}
