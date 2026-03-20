import type { Metadata } from 'next';
import Link from 'next/link';
import './globals.css';

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
        {children}
        <footer className="fixed bottom-0 w-full text-center py-2 text-xs text-text-muted bg-bg-secondary/80 backdrop-blur-sm border-t border-border-default flex items-center justify-center gap-4">
          <span>SignalFlow AI — not financial advice.</span>
          <Link href="/history" className="text-accent-purple/70 hover:text-accent-purple transition-colors">History</Link>
          <Link href="/how-it-works" className="text-accent-purple/70 hover:text-accent-purple transition-colors">How It Works</Link>
        </footer>
      </body>
    </html>
  );
}
