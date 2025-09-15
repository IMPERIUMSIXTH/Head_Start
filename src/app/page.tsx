"use client";

import { useState, useEffect } from 'react';
import InteractiveDashboard from './components/InteractiveDashboard';

export default function Home() {
  const [animatedText, setAnimatedText] = useState('');
  const fullText = 'Welcome to HeadStart';

  useEffect(() => {
    let i = 0;
    const timer = setInterval(() => {
      if (i < fullText.length) {
        setAnimatedText(fullText.slice(0, i + 1));
        i++;
      } else {
        clearInterval(timer);
      }
    }, 100);
    return () => clearInterval(timer);
  }, []);

  return (
    <main className="min-h-screen bg-gradient-to-r from-blue-50 to-indigo-100 p-12">
      <header className="max-w-5xl mx-auto mb-12 text-center">
        <h1 className="text-5xl font-extrabold text-indigo-900 mb-4">
          {animatedText}
          <span className="inline-block ml-2">🚀</span>
        </h1>
        <p className="text-lg text-indigo-700">Your AI-powered learning companion</p>
      </header>
      <section className="max-w-5xl mx-auto">
        <InteractiveDashboard />
      </section>
      <footer className="max-w-5xl mx-auto mt-16 text-center text-indigo-700">
        <p>By <span className="font-bold">HeadStart Team</span></p>
      </footer>
    </main>
  );
}
