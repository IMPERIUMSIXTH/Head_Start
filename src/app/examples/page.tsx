import Link from 'next/link';

export default function ExamplesPage() {
  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-yellow-600 text-white py-16">
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="text-5xl font-extrabold mb-4">Examples</h1>
          <p className="text-xl">Discover and deploy examples of HeadStart in action</p>
        </div>
      </header>
      <section className="max-w-5xl mx-auto py-12 px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold text-yellow-800 mb-4">Sample Projects</h2>
            <p className="text-gray-600 mb-4">Explore ready-to-use projects demonstrating HeadStart capabilities.</p>
            <ul className="list-disc list-inside text-gray-600">
              <li>AI-powered recommendation engine</li>
              <li>Content personalization</li>
              <li>Deployment automation</li>
            </ul>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold text-yellow-800 mb-4">Community Examples</h2>
            <p className="text-gray-600 mb-4">See what others have built with HeadStart.</p>
            <ul className="list-disc list-inside text-gray-600">
              <li>Open source projects</li>
              <li>Integrations and plugins</li>
              <li>Custom workflows</li>
            </ul>
          </div>
        </div>
        <div className="text-center">
          <Link href="/" className="inline-block bg-yellow-600 text-white px-6 py-3 rounded-lg hover:bg-yellow-700 transition-colors">Back to Home</Link>
        </div>
      </section>
    </main>
  );
}
