'use client';

import { useSession } from 'next-auth/react';
import { useEffect } from 'react';
import { useUserStore } from '@/store/userStore';

/**
 * Syncs the backend JWT from the NextAuth session into sessionStorage
 * so that api.ts and websocket.ts can use it for authenticated requests.
 */
export function SessionSync() {
  const { data: session } = useSession();
  const setTokens = useUserStore((s) => s.setTokens);
  const logout = useUserStore((s) => s.logout);

  useEffect(() => {
    const accessToken = (session as { accessToken?: string } | null)?.accessToken;
    const refreshToken = (session as { refreshToken?: string } | null)?.refreshToken;

    if (accessToken && refreshToken) {
      setTokens(accessToken, refreshToken);
    } else if (!session) {
      logout();
    }
  }, [session, setTokens, logout]);

  return null;
}
