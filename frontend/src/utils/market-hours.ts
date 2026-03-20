/**
 * Market hours logic for NSE, crypto, and forex.
 * All times reference IST (Asia/Kolkata, UTC+5:30).
 */

function getISTDate(): Date {
  return new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
}

/**
 * Check if NSE/BSE is currently open.
 * Hours: Mon-Fri 9:15 AM – 3:30 PM IST.
 */
export function isNSEOpen(): boolean {
  const now = getISTDate();
  const day = now.getDay();
  if (day === 0 || day === 6) return false; // Weekend

  const hours = now.getHours();
  const minutes = now.getMinutes();
  const time = hours * 60 + minutes;

  return time >= 9 * 60 + 15 && time <= 15 * 60 + 30;
}

/**
 * Crypto markets are always open (24/7).
 */
export function isCryptoOpen(): boolean {
  return true;
}

/**
 * Check if forex markets are open.
 * Hours: Sun 5:30 PM IST – Sat 3:30 AM IST (24/5).
 */
export function isForexOpen(): boolean {
  const now = getISTDate();
  const day = now.getDay();
  const hours = now.getHours();
  const minutes = now.getMinutes();
  const time = hours * 60 + minutes;

  // Closed Saturday after 3:30 AM IST
  if (day === 6 && time > 3 * 60 + 30) return false;
  // Closed all day Saturday (after 3:30 AM) and Sunday until 5:30 PM
  if (day === 0 && time < 17 * 60 + 30) return false;

  return true;
}

/**
 * Get a human-readable market status string.
 */
export function getMarketStatus(marketType: string): { isOpen: boolean; label: string } {
  switch (marketType) {
    case 'stock':
      return { isOpen: isNSEOpen(), label: isNSEOpen() ? 'Market Open' : 'Market Closed' };
    case 'crypto':
      return { isOpen: true, label: '24/7' };
    case 'forex':
      return { isOpen: isForexOpen(), label: isForexOpen() ? 'Market Open' : 'Market Closed' };
    default:
      return { isOpen: false, label: 'Unknown' };
  }
}
