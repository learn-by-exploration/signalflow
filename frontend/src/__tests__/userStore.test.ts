import { describe, it, expect, beforeEach } from 'vitest';
import { useUserStore } from '@/store/userStore';

// Mock localStorage
const store: Record<string, string> = {};
Object.defineProperty(globalThis, 'localStorage', {
  value: {
    getItem: (key: string) => store[key] ?? null,
    setItem: (key: string, val: string) => { store[key] = val; },
    removeItem: (key: string) => { delete store[key]; },
    clear: () => { Object.keys(store).forEach((k) => delete store[k]); },
  },
  writable: true,
});

describe('userStore', () => {
  beforeEach(() => {
    Object.keys(store).forEach((k) => delete store[k]);
    useUserStore.setState({ chatId: null });
  });

  it('starts with null chatId', () => {
    expect(useUserStore.getState().chatId).toBeNull();
  });

  it('setChatId stores the ID and persists to localStorage', () => {
    useUserStore.getState().setChatId(123456789);
    expect(useUserStore.getState().chatId).toBe(123456789);
    expect(store['signalflow_chat_id']).toBe('123456789');
  });

  it('clearChatId removes the ID and clears localStorage', () => {
    useUserStore.getState().setChatId(999);
    useUserStore.getState().clearChatId();
    expect(useUserStore.getState().chatId).toBeNull();
    expect(store['signalflow_chat_id']).toBeUndefined();
  });

  it('setChatId overwrites previous value', () => {
    useUserStore.getState().setChatId(111);
    useUserStore.getState().setChatId(222);
    expect(useUserStore.getState().chatId).toBe(222);
    expect(store['signalflow_chat_id']).toBe('222');
  });
});
