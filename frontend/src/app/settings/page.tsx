'use client';

import { useState, useEffect } from 'react';
import { useSession, signOut } from 'next-auth/react';
import Link from 'next/link';
import { useUserStore } from '@/store/userStore';
import { usePreferencesStore, type ViewMode, type TextSize, type ThemeMode } from '@/store/preferencesStore';
import { isNotificationSupported, getNotificationPermission, requestNotificationPermission } from '@/lib/notifications';
import type { MarketType } from '@/lib/types';

const VIEW_OPTIONS: { value: ViewMode; label: string; desc: string }[] = [
  { value: 'simple', label: 'Simple', desc: 'Symbol, action, AI reason' },
  { value: 'standard', label: 'Standard', desc: 'Full signal details' },
];

const TEXT_SIZES: { value: TextSize; label: string; cls: string }[] = [
  { value: 'small', label: 'A', cls: 'text-xs' },
  { value: 'medium', label: 'A', cls: 'text-sm' },
  { value: 'large', label: 'A', cls: 'text-base' },
];

export default function SettingsPage() {
  const { data: session } = useSession();
  const chatId = useUserStore((s) => s.chatId);
  const setChatId = useUserStore((s) => s.setChatId);
  const { viewMode, setViewMode, textSize, setTextSize, themeMode, setThemeMode, defaultMarketFilter, setDefaultMarketFilter } = usePreferencesStore();

  const [saved, setSaved] = useState(false);
  const [chatIdInput, setChatIdInput] = useState('');
  const [notifPermission, setNotifPermission] = useState<string>('default');

  useEffect(() => {
    if (chatId) setChatIdInput(String(chatId));
    setNotifPermission(getNotificationPermission());
  }, [chatId]);

  function flash() {
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }

  function handleSaveChatId() {
    const id = parseInt(chatIdInput, 10);
    if (id > 0) {
      setChatId(id);
      flash();
    }
  }

  async function handleEnableNotifications() {
    const result = await requestNotificationPermission();
    setNotifPermission(result);
  }

  function resetSettings() {
    setViewMode('standard');
    setTextSize('medium');
    setThemeMode('dark');
    setDefaultMarketFilter('all');
    flash();
  }

  return (
    <main className="min-h-screen pb-12">
      <div className="max-w-3xl mx-auto px-4 py-6 space-y-8">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-display font-semibold">Settings</h1>
          {saved && (
            <span className="text-xs text-signal-buy bg-signal-buy/10 px-3 py-1 rounded-full animate-pulse">
              ✓ Saved
            </span>
          )}
        </div>

        {/* Account Section */}
        <section className="bg-bg-card border border-border-default rounded-xl p-5 space-y-4">
          <h2 className="text-base font-display font-semibold">👤 Account</h2>
          {session?.user ? (
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-text-primary">{session.user.name}</p>
                <p className="text-xs text-text-muted">{session.user.email}</p>
              </div>
              <button
                onClick={() => signOut({ callbackUrl: '/auth/signin' })}
                className="px-3 py-1.5 text-xs rounded-lg border border-signal-sell/30 text-signal-sell hover:bg-signal-sell/10 transition-colors"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <p className="text-sm text-text-muted">Not signed in</p>
              <Link
                href="/auth/signin"
                className="px-3 py-1.5 text-xs rounded-lg border border-accent-purple text-accent-purple hover:bg-accent-purple/10 transition-colors"
              >
                Sign In
              </Link>
            </div>
          )}
        </section>

        {/* Display Preferences */}
        <section className="bg-bg-card border border-border-default rounded-xl p-5 space-y-4">
          <h2 className="text-base font-display font-semibold">🎨 Display</h2>

          <SettingRow label="Theme" description="Choose your interface theme">
            <div className="flex gap-2">
              {([
                { value: 'dark' as ThemeMode, label: '🌙 Dark' },
                { value: 'light' as ThemeMode, label: '☀️ Light' },
              ]).map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => { setThemeMode(opt.value); flash(); }}
                  className={`px-3 py-1.5 rounded-lg border text-xs transition-colors ${
                    themeMode === opt.value
                      ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                      : 'border-border-default text-text-secondary hover:border-border-hover'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </SettingRow>

          <SettingRow label="View Mode" description="Signal card detail level">
            <div className="flex gap-2">
              {VIEW_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => { setViewMode(opt.value); flash(); }}
                  className={`px-3 py-1.5 rounded-lg border text-xs transition-colors ${
                    viewMode === opt.value
                      ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                      : 'border-border-default text-text-secondary hover:border-border-hover'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </SettingRow>

          <SettingRow label="Text Size" description="Adjust text size across the app">
            <div className="flex gap-2">
              {TEXT_SIZES.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => { setTextSize(opt.value); flash(); }}
                  className={`w-9 h-9 rounded-lg border transition-colors ${opt.cls} font-display font-bold ${
                    textSize === opt.value
                      ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                      : 'border-border-default text-text-secondary hover:border-border-hover'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </SettingRow>
        </section>

        {/* Signal Preferences */}
        <section className="bg-bg-card border border-border-default rounded-xl p-5 space-y-4">
          <h2 className="text-base font-display font-semibold">📊 Signals</h2>

          <SettingRow label="Default Market Filter" description="Pre-select a market when viewing signals">
            <select
              value={defaultMarketFilter}
              onChange={(e) => { setDefaultMarketFilter(e.target.value as 'all' | MarketType); flash(); }}
              className="bg-bg-secondary border border-border-default rounded-lg px-3 py-1.5 text-sm text-text-primary"
            >
              <option value="all">All Markets</option>
              <option value="stock">Stocks</option>
              <option value="crypto">Crypto</option>
              <option value="forex">Forex</option>
            </select>
          </SettingRow>
        </section>

        {/* Notifications */}
        <section className="bg-bg-card border border-border-default rounded-xl p-5 space-y-4">
          <h2 className="text-base font-display font-semibold">🔔 Notifications</h2>

          {isNotificationSupported() && (
            <SettingRow label="Push Notifications" description="Desktop alerts for high-confidence signals">
              {notifPermission === 'granted' ? (
                <span className="text-xs text-signal-buy bg-signal-buy/10 px-3 py-1.5 rounded-lg">🔔 Enabled</span>
              ) : notifPermission === 'denied' ? (
                <span className="text-xs text-text-muted">🔕 Blocked by browser</span>
              ) : (
                <button
                  onClick={handleEnableNotifications}
                  className="px-3 py-1.5 text-xs rounded-lg border border-accent-purple/30 text-accent-purple hover:bg-accent-purple/10 transition-colors"
                >
                  Enable
                </button>
              )}
            </SettingRow>
          )}
        </section>

        {/* Telegram */}
        <section className="bg-bg-card border border-border-default rounded-xl p-5 space-y-4">
          <h2 className="text-base font-display font-semibold">💬 Telegram Integration</h2>
          <p className="text-xs text-text-muted">
            Connect your Telegram to receive signal alerts. Message{' '}
            <span className="text-accent-purple">@SignalFlowBot</span> with <code className="text-accent-purple">/start</code> to get your Chat ID.
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              inputMode="numeric"
              value={chatIdInput}
              onChange={(e) => setChatIdInput(e.target.value)}
              placeholder="Your Telegram Chat ID"
              className="flex-1 bg-bg-secondary border border-border-default rounded-lg px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple"
            />
            <button
              onClick={handleSaveChatId}
              className="px-4 py-2 text-sm bg-accent-purple text-white rounded-lg hover:bg-accent-purple/90 transition-colors"
            >
              Save
            </button>
          </div>
          {chatId && chatId > 0 && (
            <p className="text-xs text-signal-buy">✓ Telegram connected (Chat ID: {chatId})</p>
          )}
        </section>

        {/* Reset */}
        <section className="bg-bg-card border border-signal-sell/20 rounded-xl p-5 space-y-4">
          <h2 className="text-base font-display font-semibold text-signal-sell">⚠️ Reset</h2>
          <div className="flex items-center justify-between">
            <p className="text-xs text-text-muted">Reset all settings to defaults</p>
            <button
              onClick={resetSettings}
              className="px-3 py-1.5 text-xs rounded-lg border border-signal-sell/30 text-signal-sell hover:bg-signal-sell/10 transition-colors"
            >
              Reset to Defaults
            </button>
          </div>
        </section>

        {/* App Info */}
        <div className="text-center text-xs text-text-muted space-y-1 pt-4">
          <p>SignalFlow AI v1.1.0</p>
          <p>AI-generated signals for educational purposes only. Not financial advice.</p>
        </div>
      </div>
    </main>
  );
}

function SettingRow({ label, description, children }: { label: string; description: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <div className="flex-1 min-w-0">
        <p className="text-sm text-text-primary">{label}</p>
        <p className="text-xs text-text-muted">{description}</p>
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}
