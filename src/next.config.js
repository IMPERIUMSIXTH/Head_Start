/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React strict mode for better development experience
  reactStrictMode: true,
  
  // Enable SWC minification for better performance
  swcMinify: true,
  
  // Configure images domain for external content
  images: {
    domains: [
      'img.youtube.com',
      'i.ytimg.com',
      'arxiv.org',
      'localhost'
    ],
    formats: ['image/webp', 'image/avif'],
  },
  
  // Environment variables to expose to the client
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_APP_NAME: process.env.NEXT_PUBLIC_APP_NAME || 'HeadStart',
  },
  
  // Security headers
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'strict-origin-when-cross-origin',
          },
          {
            key: 'Permissions-Policy',
            value: 'camera=(), microphone=(), geolocation=()',
          },
        ],
      },
    ];
  },
  
  // Redirects for better SEO
  async redirects() {
    return [
      {
        source: '/home',
        destination: '/',
        permanent: true,
      },
    ];
  },
  
  // Webpack configuration for better bundle optimization
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // Optimize bundle size
    if (!dev && !isServer) {
      config.optimization.splitChunks.chunks = 'all';
    }
    
    return config;
  },
  
  // Enable experimental features
  experimental: {
    // Enable app directory (Next.js 13+)
    appDir: false, // Using pages directory for now
    
    // Enable server components
    serverComponentsExternalPackages: [],
  },
  
  // TypeScript configuration
  typescript: {
    // Type checking is handled by CI/CD pipeline
    ignoreBuildErrors: false,
  },
  
  // ESLint configuration
  eslint: {
    // ESLint is handled by CI/CD pipeline
    ignoreDuringBuilds: false,
  },
  
  // Output configuration for Docker
  output: 'standalone',
  
  // Compression
  compress: true,
  
  // Power by header
  poweredByHeader: false,
};

module.exports = nextConfig;

// Updated 2025-09-05: Next.js configuration with security headers and optimization settings