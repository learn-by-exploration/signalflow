export { default } from 'next-auth/middleware';

export const config = {
  matcher: [
    /*
     * Protected routes — require sign-in.
     *
     * Public routes (no auth required):
     * - / (landing page handles auth client-side)
     * - /auth/*, /shared/*, /how-it-works, /privacy, /terms, /contact,
     *   /pricing, /refund-policy
     */
    '/track-record/:path*',
    '/history/:path*',
    '/watchlist/:path*',
    '/calendar/:path*',
    '/portfolio/:path*',
    '/alerts/:path*',
    '/backtest/:path*',
    '/brief/:path*',
    '/settings/:path*',
    '/signal/:path*',
  ],
};
