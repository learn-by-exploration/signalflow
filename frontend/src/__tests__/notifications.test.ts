import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  isNotificationSupported,
  getNotificationPermission,
  requestNotificationPermission,
  showSignalNotification,
  type SignalNotificationData,
} from '@/lib/notifications';

describe('notifications', () => {
  const originalNotification = globalThis.Notification;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    // Restore original Notification
    if (originalNotification) {
      globalThis.Notification = originalNotification;
    }
  });

  describe('isNotificationSupported', () => {
    it('returns true when Notification API exists', () => {
      // jsdom may or may not have Notification, so we ensure it
      globalThis.Notification = vi.fn() as unknown as typeof Notification;
      expect(isNotificationSupported()).toBe(true);
    });

    it('returns false when Notification API is missing', () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (globalThis as any).Notification;
      expect(isNotificationSupported()).toBe(false);
      // Restore for other tests
      globalThis.Notification = originalNotification;
    });
  });

  describe('getNotificationPermission', () => {
    it('returns permission status', () => {
      const mockNotif = vi.fn() as unknown as typeof Notification;
      Object.defineProperty(mockNotif, 'permission', { value: 'granted', configurable: true });
      globalThis.Notification = mockNotif;
      expect(getNotificationPermission()).toBe('granted');
    });

    it('returns unsupported when API not available', () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (globalThis as any).Notification;
      expect(getNotificationPermission()).toBe('unsupported');
      globalThis.Notification = originalNotification;
    });
  });

  describe('requestNotificationPermission', () => {
    it('returns granted when already granted', async () => {
      const mockNotif = vi.fn() as unknown as typeof Notification;
      Object.defineProperty(mockNotif, 'permission', { value: 'granted', configurable: true });
      mockNotif.requestPermission = vi.fn();
      globalThis.Notification = mockNotif;
      const result = await requestNotificationPermission();
      expect(result).toBe('granted');
      expect(mockNotif.requestPermission).not.toHaveBeenCalled();
    });

    it('returns denied when already denied', async () => {
      const mockNotif = vi.fn() as unknown as typeof Notification;
      Object.defineProperty(mockNotif, 'permission', { value: 'denied', configurable: true });
      mockNotif.requestPermission = vi.fn();
      globalThis.Notification = mockNotif;
      const result = await requestNotificationPermission();
      expect(result).toBe('denied');
      expect(mockNotif.requestPermission).not.toHaveBeenCalled();
    });

    it('calls requestPermission when default', async () => {
      const mockNotif = vi.fn() as unknown as typeof Notification;
      Object.defineProperty(mockNotif, 'permission', { value: 'default', configurable: true });
      mockNotif.requestPermission = vi.fn().mockResolvedValue('granted');
      globalThis.Notification = mockNotif;
      const result = await requestNotificationPermission();
      expect(result).toBe('granted');
      expect(mockNotif.requestPermission).toHaveBeenCalled();
    });

    it('returns unsupported when API not available', async () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (globalThis as any).Notification;
      const result = await requestNotificationPermission();
      expect(result).toBe('unsupported');
      globalThis.Notification = originalNotification;
    });
  });

  describe('showSignalNotification', () => {
    const baseSignal: SignalNotificationData = {
      symbol: 'HDFCBANK',
      signal_type: 'STRONG_BUY',
      confidence: 92,
      current_price: '1678.90',
      target_price: '1780.00',
    };

    it('creates notification for high-confidence signal', () => {
      const mockConstructor = vi.fn();
      Object.defineProperty(mockConstructor, 'permission', { value: 'granted', configurable: true });
      globalThis.Notification = mockConstructor as unknown as typeof Notification;

      showSignalNotification(baseSignal);
      expect(mockConstructor).toHaveBeenCalledTimes(1);
      expect(mockConstructor.mock.calls[0][0]).toContain('STRONGLY BULLISH');
      expect(mockConstructor.mock.calls[0][0]).toContain('HDFCBANK');
    });

    it('skips notification for low-confidence signal', () => {
      const mockConstructor = vi.fn();
      Object.defineProperty(mockConstructor, 'permission', { value: 'granted', configurable: true });
      globalThis.Notification = mockConstructor as unknown as typeof Notification;

      showSignalNotification({ ...baseSignal, confidence: 50 });
      expect(mockConstructor).not.toHaveBeenCalled();
    });

    it('skips notification when permission not granted', () => {
      const mockConstructor = vi.fn();
      Object.defineProperty(mockConstructor, 'permission', { value: 'denied', configurable: true });
      globalThis.Notification = mockConstructor as unknown as typeof Notification;

      showSignalNotification(baseSignal);
      expect(mockConstructor).not.toHaveBeenCalled();
    });

    it('respects custom minConfidence threshold', () => {
      const mockConstructor = vi.fn();
      Object.defineProperty(mockConstructor, 'permission', { value: 'granted', configurable: true });
      globalThis.Notification = mockConstructor as unknown as typeof Notification;

      showSignalNotification({ ...baseSignal, confidence: 85 }, 90);
      expect(mockConstructor).not.toHaveBeenCalled();

      showSignalNotification({ ...baseSignal, confidence: 91 }, 90);
      expect(mockConstructor).toHaveBeenCalledTimes(1);
    });

    it('includes price and target in body', () => {
      const mockConstructor = vi.fn();
      Object.defineProperty(mockConstructor, 'permission', { value: 'granted', configurable: true });
      globalThis.Notification = mockConstructor as unknown as typeof Notification;

      showSignalNotification(baseSignal);
      const body = mockConstructor.mock.calls[0][1].body;
      expect(body).toContain('1678.90');
      expect(body).toContain('1780.00');
      expect(body).toContain('92%');
    });
  });
});
