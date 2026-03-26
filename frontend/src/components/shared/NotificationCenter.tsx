'use client';

import { useState, useRef, useEffect } from 'react';

interface NotificationItem {
  id: string;
  title: string;
  body: string;
  type: 'signal' | 'alert' | 'system';
  timestamp: Date;
  read: boolean;
}

const STORAGE_KEY = 'sf_notifications';
const MAX_NOTIFICATIONS = 50;

function loadNotifications(): NotificationItem[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const items = JSON.parse(raw) as NotificationItem[];
    return items.map((n) => ({ ...n, timestamp: new Date(n.timestamp) }));
  } catch {
    return [];
  }
}

function saveNotifications(items: NotificationItem[]) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, MAX_NOTIFICATIONS)));
}

export function addNotification(title: string, body: string, type: NotificationItem['type'] = 'signal') {
  const items = loadNotifications();
  const newItem: NotificationItem = {
    id: `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    title,
    body,
    type,
    timestamp: new Date(),
    read: false,
  };
  saveNotifications([newItem, ...items]);
  // Dispatch event for live updates
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent('sf-notification', { detail: newItem }));
  }
}

export function NotificationCenter() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const panelRef = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter((n) => !n.read).length;

  useEffect(() => {
    setNotifications(loadNotifications());

    function handleNew() {
      setNotifications(loadNotifications());
    }

    window.addEventListener('sf-notification', handleNew);
    return () => window.removeEventListener('sf-notification', handleNew);
  }, []);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    if (isOpen) document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  function markAllRead() {
    const updated = notifications.map((n) => ({ ...n, read: true }));
    setNotifications(updated);
    saveNotifications(updated);
  }

  function clearAll() {
    setNotifications([]);
    saveNotifications([]);
  }

  function formatTime(date: Date): string {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    return `${Math.floor(hours / 24)}d ago`;
  }

  const typeIcon: Record<string, string> = {
    signal: '📊',
    alert: '🔔',
    system: '⚙️',
  };

  return (
    <div ref={panelRef} className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-text-secondary hover:text-text-primary transition-colors"
        aria-label={`Notifications${unreadCount > 0 ? ` (${unreadCount} unread)` : ''}`}
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
        {unreadCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 w-4 h-4 bg-signal-sell text-white text-[10px] font-bold rounded-full flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-80 max-h-96 bg-bg-secondary border border-border-default rounded-xl shadow-2xl z-50 overflow-hidden flex flex-col">
          <div className="flex items-center justify-between px-4 py-3 border-b border-border-default">
            <h3 className="text-sm font-display font-semibold">Notifications</h3>
            <div className="flex gap-2">
              {unreadCount > 0 && (
                <button onClick={markAllRead} className="text-[10px] text-accent-purple hover:underline">
                  Mark all read
                </button>
              )}
              {notifications.length > 0 && (
                <button onClick={clearAll} className="text-[10px] text-text-muted hover:text-signal-sell">
                  Clear
                </button>
              )}
            </div>
          </div>

          <div className="overflow-y-auto flex-1">
            {notifications.length === 0 ? (
              <div className="px-4 py-8 text-center text-sm text-text-muted">
                <span className="text-2xl block mb-2">🔔</span>
                No notifications yet
              </div>
            ) : (
              notifications.slice(0, 20).map((n) => (
                <div
                  key={n.id}
                  className={`px-4 py-3 border-b border-border-default/50 hover:bg-bg-card transition-colors ${
                    !n.read ? 'bg-accent-purple/5' : ''
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-sm mt-0.5">{typeIcon[n.type] ?? '📊'}</span>
                    <div className="flex-1 min-w-0">
                      <p className={`text-xs ${!n.read ? 'font-medium text-text-primary' : 'text-text-secondary'}`}>
                        {n.title}
                      </p>
                      <p className="text-[11px] text-text-muted mt-0.5 truncate">{n.body}</p>
                      <p className="text-[10px] text-text-muted mt-1">{formatTime(n.timestamp)}</p>
                    </div>
                    {!n.read && (
                      <span className="w-2 h-2 rounded-full bg-accent-purple mt-1 shrink-0" />
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
