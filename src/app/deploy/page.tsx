import Link from 'next/link';

export default function DeployPage() {
  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-purple-600 text-white py-16">
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="text-5xl font-extrabold mb-4">Deploy</h1>
          <p className="text-xl">Instantly deploy your HeadStart app to production</p>
        </div>
      </header>
      <section className="max-w-5xl mx-auto py-12 px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold text-purple-800 mb-4">One-Click Deployment</h2>
            <p className="text-gray-600 mb-4">Deploy to popular platforms with a single click.</p>
            <ul className="list-disc list-inside text-gray-600">
              <li>Vercel integration</li>
              <li>Netlify support</li>
              <li>Docker containers</li>
            </ul>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold text-purple-800 mb-4">Advanced Options</h2>
            <p className="text-gray-600 mb-4">Customize your deployment for specific needs.</p>
            <ul className="list-disc list-inside text-gray-600">
              <li>Environment variables</li>
              <li>Custom domains</li>
              <li>SSL certificates</li>
            </ul>
          </div>
        </div>
        <div className="text-center">
          <Link href="/" className="inline-block bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors">Back to Home</Link>
        </div>
      </section>
    </main>
  );
}
