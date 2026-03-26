/**
 * Zustand store for user identity and JWT authentication.
 */

import { create } from 'zustand';

const TOKEN_KEY = 'signalflow_access_token';
const REFRESH_KEY = 'signalflow_refresh_token';
const CHAT_ID_KEY = 'signalflow_chat_id';

interface UserState {
  chatId: number | null;
  accessToken: string | null;
  refreshToken: string | null;
  tier: string;
  isAuthenticated: boolean;
  setChatId: (id: number) => void;
  clearChatId: () => void;
  setTokens: (access: string, refresh: string) => void;
  setTier: (tier: string) => void;
  logout: () => void;
}

function getStored(key: string): string | null {
  if (typeof window === 'undefined') return null;
  return sessionStorage.getItem(key);
}

function getStoredChatId(): number | null {
  if (typeof window === 'undefined') return null;
  // chatId persists in localStorage (survives tab close)
  const stored = localStorage.getItem(CHAT_ID_KEY);
  if (stored) {
    const num = parseInt(stored, 10);
    return isNaN(num) ? null : num;
  }
  return null;
}

export const useUserStore = create<UserState>((set) => ({
  chatId: getStoredChatId(),
  accessToken: getStored(TOKEN_KEY),
  refreshToken: getStored(REFRESH_KEY),
  tier: 'free',
  isAuthenticated: !!getStored(TOKEN_KEY),

  setChatId: (id: number) => {
    localStorage.setItem(CHAT_ID_KEY, String(id));
    set({ chatId: id });
  },

  clearChatId: () => {
    localStorage.removeItem(CHAT_ID_KEY);
    set({ chatId: null });
  },

  setTokens: (access: string, refresh: string) => {
    sessionStorage.setItem(TOKEN_KEY, access);
    sessionStorage.setItem(REFRESH_KEY, refresh);
    set({ accessToken: access, refreshToken: refresh, isAuthenticated: true });
  },

  setTier: (tier: string) => {
    set({ tier });
  },

  logout: () => {
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(CHAT_ID_KEY);
    set({ accessToken: null, refreshToken: null, chatId: null, tier: 'free', isAuthenticated: false });
  },
}));
