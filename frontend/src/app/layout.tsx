import type { Metadata } from 'next';
import './globals.css';
import { Navbar } from '@/components/shared/Navbar';
import { ToastProvider } from '@/components/shared/Toast';

export const metadata: Metadata = {
  title: 'SignalFlow AI — Trading Signals',
  description: 'AI-powered trading signal platform for Indian Stocks, Crypto, and Forex',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-bg-primary text-text-primary font-body antialiased">
        <ToastProvider>
          <Navbar />
          {children}
          <footer className="fixed bottom-0 w-full text-center py-2 text-xs text-text-muted bg-bg-secondary/80 backdrop-blur-sm border-t border-border-default">
            <span>⚠️ SignalFlow AI — AI-generated analysis, not financial advice. Always do your own research.</span>
          </footer>
        </ToastProvider>
      </body>
    </html>
  );
}
