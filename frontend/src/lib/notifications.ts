/**
 * Browser push notification utility for high-confidence signals.
 * Uses the Notification API with graceful fallback when unavailable.
 */

const SIGNAL_EMOJIS: Record<string, string> = {
  STRONG_BUY: '🟢',
  BUY: '🟢',
  HOLD: '🟡',
  SELL: '🔴',
  STRONG_SELL: '🔴',
};

export function isNotificationSupported(): boolean {
  return typeof window !== 'undefined' && 'Notification' in window;
}

export function getNotificationPermission(): NotificationPermission | 'unsupported' {
  if (!isNotificationSupported()) return 'unsupported';
  return Notification.permission;
}

export async function requestNotificationPermission(): Promise<NotificationPermission | 'unsupported'> {
  if (!isNotificationSupported()) return 'unsupported';
  if (Notification.permission === 'granted') return 'granted';
  if (Notification.permission === 'denied') return 'denied';
  return Notification.requestPermission();
}

export interface SignalNotificationData {
  symbol: string;
  signal_type: string;
  confidence: number;
  current_price: string;
  target_price: string;
}

/**
 * Show a browser notification for a new signal.
 * Only fires for signals with confidence >= minConfidence.
 */
export function showSignalNotification(signal: SignalNotificationData, minConfidence = 70): void {
  if (!isNotificationSupported()) return;
  if (Notification.permission !== 'granted') return;
  if (signal.confidence < minConfidence) return;

  const emoji = SIGNAL_EMOJIS[signal.signal_type] ?? '📊';
  const displayLabels: Record<string, string> = {
    STRONG_BUY: 'STRONGLY BULLISH',
    BUY: 'BULLISH',
    HOLD: 'HOLD',
    SELL: 'BEARISH',
    STRONG_SELL: 'STRONGLY BEARISH',
  };
  const label = displayLabels[signal.signal_type] ?? signal.signal_type;
  const title = `${emoji} ${label} — ${signal.symbol}`;
  const body = `Confidence: ${signal.confidence}%\nPrice: ${signal.current_price} → Target: ${signal.target_price}`;

  new Notification(title, {
    body,
    icon: '/favicon.ico',
    tag: `signal-${signal.symbol}-${Date.now()}`,
    silent: false,
  });
}
