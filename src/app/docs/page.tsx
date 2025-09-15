import Link from 'next/link';

export default function DocsPage() {
  return (
    <main className="min-h-screen bg-gray-50">
      <header className="bg-indigo-600 text-white py-16">
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="text-5xl font-extrabold mb-4">Documentation</h1>
          <p className="text-xl">In-depth information about HeadStart features and API</p>
        </div>
      </header>
      <section className="max-w-5xl mx-auto py-12 px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-12">
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold text-indigo-800 mb-4">Getting Started</h2>
            <p className="text-gray-600 mb-4">Learn how to set up and configure HeadStart for your project.</p>
            <Link href="#getting-started" className="text-indigo-600 hover:underline">Read more &rarr;</Link>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold text-indigo-800 mb-4">API Reference</h2>
            <p className="text-gray-600 mb-4">Detailed API documentation for developers.</p>
            <Link href="#api-reference" className="text-indigo-600 hover:underline">Read more &rarr;</Link>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-semibold text-indigo-800 mb-4">Tutorials</h2>
            <p className="text-gray-600 mb-4">Step-by-step guides to common tasks.</p>
            <Link href="#tutorials" className="text-indigo-600 hover:underline">Read more &rarr;</Link>
          </div>
        </div>
        <div className="text-center">
          <Link href="/" className="inline-block bg-indigo-600 text-white px-6 py-3 rounded-lg hover:bg-indigo-700 transition-colors">Back to Home</Link>
        </div>
      </section>
    </main>
  );
}
