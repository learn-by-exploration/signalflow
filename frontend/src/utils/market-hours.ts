/**
 * Market hours logic for NSE, crypto, and forex.
 * All times reference IST (Asia/Kolkata, UTC+5:30).
 */

function getISTDate(): Date {
  return new Date(new Date().toLocaleString('en-US', { timeZone: 'Asia/Kolkata' }));
}

/**
 * NSE holidays for 2025-2026.
 * Format: 'MM-DD' for recurring checks and 'YYYY-MM-DD' for exact dates.
 * Source: NSE circular — national/exchange holidays when market is closed.
 */
const NSE_HOLIDAYS: string[] = [
  // 2025
  '2025-01-26', // Republic Day
  '2025-02-26', // Maha Shivaratri
  '2025-03-14', // Holi
  '2025-03-31', // Id-ul-Fitr (Ramadan)
  '2025-04-10', // Shri Mahavir Jayanti
  '2025-04-14', // Dr. Ambedkar Jayanti
  '2025-04-18', // Good Friday
  '2025-05-01', // Maharashtra Day
  '2025-06-07', // Id-ul-Adha (Bakri Id)
  '2025-08-15', // Independence Day
  '2025-08-16', // Parsi New Year
  '2025-08-27', // Ganesh Chaturthi
  '2025-10-02', // Mahatma Gandhi Jayanti / Dussehra
  '2025-10-21', // Diwali (Laxmi Pujan)
  '2025-10-22', // Diwali Balipratipada
  '2025-11-05', // Guru Nanak Jayanti
  '2025-12-25', // Christmas
  // 2026
  '2026-01-26', // Republic Day
  '2026-02-17', // Maha Shivaratri
  '2026-03-03', // Holi
  '2026-03-20', // Id-ul-Fitr
  '2026-03-25', // Shri Mahavir Jayanti
  '2026-04-03', // Good Friday
  '2026-04-14', // Dr. Ambedkar Jayanti
  '2026-05-01', // Maharashtra Day
  '2026-05-27', // Id-ul-Adha (Bakri Id)
  '2026-08-15', // Independence Day
  '2026-08-18', // Ganesh Chaturthi
  '2026-10-02', // Mahatma Gandhi Jayanti
  '2026-10-10', // Dussehra
  '2026-11-09', // Diwali (Laxmi Pujan)
  '2026-11-10', // Diwali Balipratipada
  '2026-11-25', // Guru Nanak Jayanti
  '2026-12-25', // Christmas
];

/**
 * Check if a given date is an NSE holiday.
 */
function isNSEHoliday(date: Date): boolean {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return NSE_HOLIDAYS.includes(`${year}-${month}-${day}`);
}

/**
 * Check if NSE/BSE is currently open.
 * Hours: Mon-Fri 9:15 AM – 3:30 PM IST, excluding NSE holidays.
 */
export function isNSEOpen(): boolean {
  const now = getISTDate();
  const day = now.getDay();
  if (day === 0 || day === 6) return false; // Weekend
  if (isNSEHoliday(now)) return false; // NSE holiday

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

/**
 * Get a short status badge and next-open hint for each market.
 */
export function getMarketBadge(marketType: string): { isOpen: boolean; badge: string; hint: string | null } {
  switch (marketType) {
    case 'stock': {
      const open = isNSEOpen();
      if (open) return { isOpen: true, badge: '🟢 Open', hint: null };
      const now = getISTDate();
      const day = now.getDay();
      if (isNSEHoliday(now)) {
        return { isOpen: false, badge: '🔴 Holiday', hint: 'NSE holiday — market closed today' };
      }
      const daysUntilMon = day === 0 ? 1 : day === 6 ? 2 : 0;
      if (daysUntilMon > 0) {
        return { isOpen: false, badge: '🔴 Closed', hint: `Opens ${daysUntilMon === 1 ? 'Mon' : 'Mon'} 9:15 AM IST` };
      }
      // Weekday but after hours
      const time = now.getHours() * 60 + now.getMinutes();
      if (time < 9 * 60 + 15) return { isOpen: false, badge: '🔴 Closed', hint: 'Opens 9:15 AM IST' };
      return { isOpen: false, badge: '🔴 Closed', hint: 'Opens tomorrow 9:15 AM IST' };
    }
    case 'crypto':
      return { isOpen: true, badge: '🟢 24/7', hint: null };
    case 'forex': {
      const open = isForexOpen();
      if (open) return { isOpen: true, badge: '🟢 Open', hint: null };
      return { isOpen: false, badge: '🔴 Closed', hint: 'Opens Sun 5:30 PM IST' };
    }
    default:
      return { isOpen: false, badge: '⚪ Unknown', hint: null };
  }
}
