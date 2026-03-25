import { describe, it, expect, beforeEach } from 'vitest';
import { useUserStore } from '@/store/userStore';

// Mock sessionStorage
const store: Record<string, string> = {};
Object.defineProperty(globalThis, 'sessionStorage', {
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
    useUserStore.setState({ chatId: null, accessToken: null, refreshToken: null, isAuthenticated: false });
  });

  it('starts with null chatId', () => {
    expect(useUserStore.getState().chatId).toBeNull();
  });

  it('setChatId stores the ID and persists to sessionStorage', () => {
    useUserStore.getState().setChatId(123456789);
    expect(useUserStore.getState().chatId).toBe(123456789);
    expect(store['signalflow_chat_id']).toBe('123456789');
  });

  it('clearChatId removes the ID and clears sessionStorage', () => {
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

  it('setTokens stores tokens in sessionStorage', () => {
    useUserStore.getState().setTokens('access-123', 'refresh-456');
    expect(useUserStore.getState().accessToken).toBe('access-123');
    expect(useUserStore.getState().refreshToken).toBe('refresh-456');
    expect(useUserStore.getState().isAuthenticated).toBe(true);
    expect(store['signalflow_access_token']).toBe('access-123');
    expect(store['signalflow_refresh_token']).toBe('refresh-456');
  });

  it('logout clears all auth state', () => {
    useUserStore.getState().setTokens('access-123', 'refresh-456');
    useUserStore.getState().setChatId(999);
    useUserStore.getState().logout();
    expect(useUserStore.getState().accessToken).toBeNull();
    expect(useUserStore.getState().refreshToken).toBeNull();
    expect(useUserStore.getState().isAuthenticated).toBe(false);
    expect(useUserStore.getState().chatId).toBeNull();
  });
});
