import type { Metadata } from 'next';
import { Outfit, JetBrains_Mono } from 'next/font/google';
import './globals.css';
import { Navbar } from '@/components/shared/Navbar';
import { ToastProvider } from '@/components/shared/Toast';

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
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
        <body className={`${outfit.variable} ${jetbrainsMono.variable} min-h-screen bg-bg-primary text-text-primary font-body antialiased`}>
        <ToastProvider>
          <Navbar />
          {children}
        </ToastProvider>
      </body>
    </html>
  );
}
