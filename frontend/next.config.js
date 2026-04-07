/** @type {import('next').NextConfig} */
const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
const mkgUrl = process.env.MKG_URL || 'http://localhost:8001';

const nextConfig = {
  output: 'standalone',

  async rewrites() {
    return [
      // Proxy REST API calls to the backend
      {
        source: '/api/v1/:path*',
        destination: `${backendUrl}/api/v1/:path*`,
      },
      // Proxy health endpoint
      {
        source: '/health',
        destination: `${backendUrl}/health`,
      },
      // Proxy metrics endpoint
      {
        source: '/metrics',
        destination: `${backendUrl}/metrics`,
      },
      // Proxy WebSocket endpoint
      {
        source: '/ws/:path*',
        destination: `${backendUrl}/ws/:path*`,
      },
      // Proxy MKG API calls
      {
        source: '/mkg/api/v1/:path*',
        destination: `${mkgUrl}/api/v1/:path*`,
      },
      // Proxy MKG research library
      {
        source: '/research',
        destination: `${mkgUrl}/research/`,
      },
      {
        source: '/research/:path*',
        destination: `${mkgUrl}/research/:path*`,
      },
    ];
  },

  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          {
            key: 'Content-Security-Policy',
            value: [
              "default-src 'self'",
              // Next.js requires 'unsafe-inline' for inline scripts in production builds.
              // 'unsafe-eval' removed — not needed for production Next.js standalone output.
              "script-src 'self' 'unsafe-inline' https://checkout.razorpay.com https://plausible.io",
              "style-src 'self' 'unsafe-inline'",
              "img-src 'self' data: https:",
              "connect-src 'self' ws: wss: https://lux-gateway.razorpay.com https://api.razorpay.com https://plausible.io",
              "font-src 'self' https://fonts.gstatic.com",
              "frame-src https://api.razorpay.com",
              "frame-ancestors 'none'",
            ].join('; '),
          },
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=()' },
          { key: 'Strict-Transport-Security', value: 'max-age=31536000; includeSubDomains' },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
