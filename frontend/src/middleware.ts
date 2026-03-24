export { default } from 'next-auth/middleware';

export const config = {
  matcher: [
    /*
     * Protected routes — require sign-in:
     * - /portfolio, /alerts, /backtest, /brief
     *
     * Public routes (excluded from matcher):
     * - /, /track-record, /history, /how-it-works, /shared/*, /auth/*
     */
    '/portfolio/:path*',
    '/alerts/:path*',
    '/backtest/:path*',
    '/brief/:path*',
  ],
};
