import type { Metadata } from 'next';
import { Outfit, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { Navbar } from '@/components/shared/Navbar';
import { OfflineBanner } from '@/components/shared/OfflineBanner';
import { BottomNav } from '@/components/shared/BottomNav';
import { SiteFooter } from '@/components/shared/SiteFooter';
import { CookieConsent } from '@/components/shared/CookieConsent';
import { AuthProvider } from '@/components/shared/AuthProvider';
import { QueryProvider } from '@/components/shared/QueryProvider';
import { ToastProvider } from '@/components/shared/Toast';
import { TextSizeProvider } from '@/components/shared/TextSizeProvider';
import { ThemeProvider } from '@/components/shared/ThemeProvider';
import { ErrorBoundary } from '@/components/shared/ErrorBoundary';

const outfit = Outfit({
  subsets: ['latin'],
  variable: '--font-outfit',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-jetbrains',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'SignalFlow AI — Trading Signals',
  description: 'AI-powered trading signal platform for Indian Stocks, Crypto, and Forex',
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL || 'https://signalflow.ai'),
  openGraph: {
    title: 'SignalFlow AI — AI-Powered Trading Signals',
    description: 'Clear, actionable buy/sell signals for Indian Stocks, Crypto, and Forex — backed by AI reasoning you can trust.',
    type: 'website',
  },
  twitter: { card: 'summary_large_image' },
  robots: { index: true, follow: true },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
        <body className={`${outfit.variable} ${jetbrainsMono.variable} flex flex-col min-h-screen bg-bg-primary text-text-primary font-body antialiased`}>
        <ErrorBoundary name="App">
        <AuthProvider>
        <QueryProvider>
        <ToastProvider>
          <ThemeProvider>
            <TextSizeProvider />
            <Navbar />
            <OfflineBanner />
            <main className="flex-1 pb-[72px] md:pb-0">{children}</main>
            <BottomNav />
            <SiteFooter />
            <CookieConsent />
          </ThemeProvider>
        </ToastProvider>
        </QueryProvider>
        </AuthProvider>
        </ErrorBoundary>
      </body>
    </html>
  );
}
