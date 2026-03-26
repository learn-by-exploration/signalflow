'use client';

import { useState, useEffect } from 'react';
import { usePreferencesStore, type ViewMode, type TextSize, type ThemeMode } from '@/store/preferencesStore';
import { isNotificationSupported, getNotificationPermission, requestNotificationPermission } from '@/lib/notifications';
import { FocusTrap } from './FocusTrap';

const VIEW_OPTIONS: { value: ViewMode; label: string; desc: string }[] = [
  { value: 'simple', label: 'Simple', desc: 'Symbol, action, AI reason only' },
  { value: 'standard', label: 'Standard', desc: 'Full signal details' },
];

const TEXT_SIZES: { value: TextSize; label: string }[] = [
  { value: 'small', label: 'A' },
  { value: 'medium', label: 'A' },
  { value: 'large', label: 'A' },
];

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const { viewMode, setViewMode, textSize, setTextSize, themeMode, setThemeMode } = usePreferencesStore();
  const [notifPermission, setNotifPermission] = useState<string>('default');

  useEffect(() => {
    if (isOpen) {
      setNotifPermission(getNotificationPermission());
    }
  }, [isOpen]);

  async function handleEnableNotifications() {
    const result = await requestNotificationPermission();
    setNotifPermission(result);
  }

  if (!isOpen) return null;

  return (
    <FocusTrap isOpen={isOpen} onClose={onClose}>
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label="Settings"
        className="bg-bg-secondary border border-border-default rounded-2xl max-w-sm w-full p-6 shadow-2xl space-y-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-display font-bold">Settings</h2>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary text-sm">✕</button>
        </div>

        {/* View Mode */}
        <div>
          <label className="text-xs text-text-muted uppercase tracking-wider block mb-2">View Mode</label>
          <div className="flex gap-2">
            {VIEW_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setViewMode(opt.value)}
                className={`flex-1 px-3 py-2 rounded-lg border text-sm transition-colors ${
                  viewMode === opt.value
                    ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                    : 'border-border-default text-text-secondary hover:border-border-hover'
                }`}
              >
                <span className="font-medium block">{opt.label}</span>
                <span className="text-xs text-text-muted block mt-0.5">{opt.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Text Size */}
        <div>
          <label className="text-xs text-text-muted uppercase tracking-wider block mb-2">Text Size</label>
          <div className="flex gap-2">
            {TEXT_SIZES.map((opt, i) => {
              const fontSize = i === 0 ? 'text-xs' : i === 1 ? 'text-sm' : 'text-base';
              return (
                <button
                  key={opt.value}
                  onClick={() => setTextSize(opt.value)}
                  className={`flex-1 py-2 rounded-lg border transition-colors ${fontSize} font-display font-bold ${
                    textSize === opt.value
                      ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                      : 'border-border-default text-text-secondary hover:border-border-hover'
                  }`}
                >
                  {opt.label}
                  <span className="block text-xs font-normal text-text-muted mt-0.5">
                    {opt.value.charAt(0).toUpperCase() + opt.value.slice(1)}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Theme Mode (L-1) */}
        <div>
          <label className="text-xs text-text-muted uppercase tracking-wider block mb-2">Theme</label>
          <div className="flex gap-2">
            {[
              { value: 'dark' as ThemeMode, label: '🌙 Dark', desc: 'Trading terminal' },
              { value: 'light' as ThemeMode, label: '☀️ Light', desc: 'Easy reading' },
            ].map((opt) => (
              <button
                key={opt.value}
                onClick={() => setThemeMode(opt.value)}
                className={`flex-1 px-3 py-2 rounded-lg border text-sm transition-colors ${
                  themeMode === opt.value
                    ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                    : 'border-border-default text-text-secondary hover:border-border-hover'
                }`}
              >
                <span className="font-medium block">{opt.label}</span>
                <span className="text-xs text-text-muted block mt-0.5">{opt.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Push Notifications */}
        {isNotificationSupported() && (
          <div>
            <label className="text-xs text-text-muted uppercase tracking-wider block mb-2">Push Notifications</label>
            {notifPermission === 'granted' ? (
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-signal-buy/30 bg-signal-buy/5">
                <span className="text-signal-buy text-sm">🔔</span>
                <span className="text-xs text-signal-buy">Enabled — you&apos;ll get alerts for high-confidence signals</span>
              </div>
            ) : notifPermission === 'denied' ? (
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg border border-border-default">
                <span className="text-text-muted text-sm">🔕</span>
                <span className="text-xs text-text-muted">Blocked by browser. Enable in browser settings.</span>
              </div>
            ) : (
              <button
                onClick={handleEnableNotifications}
                className="w-full px-3 py-2 rounded-lg border border-accent-purple/30 text-accent-purple text-sm hover:bg-accent-purple/10 transition-colors"
              >
                🔔 Enable Signal Alerts
              </button>
            )}
          </div>
        )}

        <button
          onClick={onClose}
          className="w-full py-2 bg-accent-purple text-white rounded-lg text-sm font-medium hover:bg-accent-purple/90 transition-colors"
        >
          Done
        </button>
      </div>
    </div>
    </FocusTrap>
  );
}
