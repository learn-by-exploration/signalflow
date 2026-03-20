/**
 * Zustand store for user identity.
 * In MVP, uses localStorage to persist a Telegram chat ID.
 */

import { create } from 'zustand';

const STORAGE_KEY = 'signalflow_chat_id';

interface UserState {
  chatId: number | null;
  setChatId: (id: number) => void;
  clearChatId: () => void;
}

function getStoredChatId(): number | null {
  if (typeof window === 'undefined') return null;
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    const num = parseInt(stored, 10);
    return isNaN(num) ? null : num;
  }
  return null;
}

export const useUserStore = create<UserState>((set) => ({
  chatId: getStoredChatId(),
  setChatId: (id: number) => {
    localStorage.setItem(STORAGE_KEY, String(id));
    set({ chatId: id });
  },
  clearChatId: () => {
    localStorage.removeItem(STORAGE_KEY);
    set({ chatId: null });
  },
}));
