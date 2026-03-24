export { default } from 'next-auth/middleware';

export const config = {
  matcher: [
    /*
     * Protected routes — require sign-in.
     *
     * Public routes (no auth required):
     * - /auth/*, /shared/*, /how-it-works, /privacy, /terms, /contact, /track-record
     */
    '/',
    '/history/:path*',
    '/watchlist/:path*',
    '/calendar/:path*',
    '/portfolio/:path*',
    '/alerts/:path*',
    '/backtest/:path*',
    '/brief/:path*',
    '/settings/:path*',
  ],
};
