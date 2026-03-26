'use client';

import { SessionProvider as NextAuthSessionProvider } from 'next-auth/react';
import { SessionSync } from './SessionSync';

interface AuthProviderProps {
  children: React.ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  return (
    <NextAuthSessionProvider>
      <SessionSync />
      {children}
    </NextAuthSessionProvider>
  );
}
