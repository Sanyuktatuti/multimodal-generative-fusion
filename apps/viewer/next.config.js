/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  env: {
    API_BASE: process.env.API_BASE || 'http://localhost:8000',
  },
  async rewrites() {
    return [
      // Proxy API calls to backend
      {
        source: '/api/generations/:path*',
        destination: `${process.env.API_BASE || 'http://localhost:8000'}/v1/generations/:path*`
      }
    ]
  }
}

module.exports = nextConfig