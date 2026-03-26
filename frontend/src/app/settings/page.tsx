'use client';

import { useState, useEffect } from 'react';
import { useSession, signOut } from 'next-auth/react';
import Link from 'next/link';
import { useUserStore } from '@/store/userStore';
import { usePreferencesStore, type ViewMode, type TextSize, type ThemeMode } from '@/store/preferencesStore';
import { isNotificationSupported, getNotificationPermission, requestNotificationPermission } from '@/lib/notifications';
import { api } from '@/lib/api';
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
  const { viewMode, setViewMode, textSize, setTextSize, themeMode, setThemeMode, defaultMarketFilter, setDefaultMarketFilter, tradingCapital, setTradingCapital, maxRiskPct, setMaxRiskPct } = usePreferencesStore();

  const [saved, setSaved] = useState(false);
  const [chatIdInput, setChatIdInput] = useState('');
  const [notifPermission, setNotifPermission] = useState<string>('default');
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  // Password change
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [passwordMsg, setPasswordMsg] = useState<{ text: string; type: 'success' | 'error' } | null>(null);

  // Account deletion
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteMsg, setDeleteMsg] = useState<{ text: string; type: 'error' } | null>(null);

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

  async function handleChangePassword() {
    if (!currentPassword || !newPassword) return;
    setPasswordMsg(null);
    try {
      await api.changePassword({ current_password: currentPassword, new_password: newPassword });
      setPasswordMsg({ text: 'Password changed successfully!', type: 'success' });
      setCurrentPassword('');
      setNewPassword('');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to change password';
      setPasswordMsg({ text: msg, type: 'error' });
    }
  }

  async function handleDeleteAccount() {
    if (!deletePassword) return;
    setDeleteMsg(null);
    try {
      await api.deleteAccount({ password: deletePassword, confirm: true });
      signOut({ callbackUrl: '/auth/signin' });
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to delete account';
      setDeleteMsg({ text: msg, type: 'error' });
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
    setTradingCapital(0);
    setMaxRiskPct(2);
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
          <h2 className="text-base font-display font-semibold">🚀 Quick Setup</h2>
          <p className="text-xs text-text-muted">Choose a preset that matches your trading style. This adjusts display settings and recommended alert thresholds.</p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <button
              onClick={() => {
                setViewMode('simple');
                setTextSize('medium');
                setDefaultMarketFilter('stock');
                flash();
              }}
              className="p-4 rounded-xl border border-signal-buy/30 hover:border-signal-buy/60 bg-signal-buy/5 transition-colors text-left space-y-1"
            >
              <div className="flex items-center gap-2">
                <span className="text-lg">🛡️</span>
                <span className="text-sm font-semibold text-signal-buy">Conservative</span>
              </div>
              <p className="text-xs text-text-muted">Stocks only, simple cards. Best for beginners — fewer signals, higher quality.</p>
              <p className="text-xs text-text-muted mt-1 font-mono">Recommended: 80%+ confidence</p>
            </button>
            <button
              onClick={() => {
                setViewMode('standard');
                setTextSize('medium');
                setDefaultMarketFilter('all');
                flash();
              }}
              className="p-4 rounded-xl border border-accent-purple/30 hover:border-accent-purple/60 bg-accent-purple/5 transition-colors text-left space-y-1"
            >
              <div className="flex items-center gap-2">
                <span className="text-lg">⚖️</span>
                <span className="text-sm font-semibold text-accent-purple">Balanced</span>
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-accent-purple/20 text-accent-purple">Recommended</span>
              </div>
              <p className="text-xs text-text-muted">All markets, full details. Good mix of signal volume and quality.</p>
              <p className="text-xs text-text-muted mt-1 font-mono">Recommended: 70%+ confidence</p>
            </button>
            <button
              onClick={() => {
                setViewMode('standard');
                setTextSize('medium');
                setDefaultMarketFilter('all');
                flash();
              }}
              className="p-4 rounded-xl border border-signal-sell/30 hover:border-signal-sell/60 bg-signal-sell/5 transition-colors text-left space-y-1"
            >
              <div className="flex items-center gap-2">
                <span className="text-lg">🔥</span>
                <span className="text-sm font-semibold text-signal-sell">Aggressive</span>
              </div>
              <p className="text-xs text-text-muted">All markets, all signals. More opportunities, requires experience.</p>
              <p className="text-xs text-text-muted mt-1 font-mono">Recommended: 60%+ confidence</p>
            </button>
          </div>
        </section>

        {/* Display Preferences */}
        <section className="bg-bg-card border border-border-default rounded-xl p-5 space-y-4">
          <h2 className="text-base font-display font-semibold">🎨 Display</h2>

          <SettingRow label="Theme" description="Choose your interface theme" tooltip="Dark mode reduces eye strain during long trading sessions. Most traders prefer dark mode.">
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

          <SettingRow label="View Mode" description="Signal card detail level" tooltip="Simple shows just the action and AI reasoning. Standard shows technical indicators, targets, and stop-loss details.">
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

          <SettingRow label="Text Size" description="Adjust text size across the app" tooltip="Increase text size if you find prices and percentages hard to read on your screen.">
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

          <SettingRow label="Default Market Filter" description="Pre-select a market when viewing signals" tooltip="If you mostly trade Indian stocks, set this to 'Stocks' so the dashboard always opens filtered to NSE signals.">
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

        {/* Capital & Position Sizing */}
        <section className="bg-bg-card border border-border-default rounded-xl p-5 space-y-4">
          <h2 className="text-base font-display font-semibold">💰 Capital & Position Sizing</h2>
          <p className="text-xs text-text-muted">Set your trading capital and risk tolerance. SignalFlow will show recommended position sizes on each signal.</p>

          <SettingRow label="Trading Capital" description="Your total capital available for trading" tooltip="Enter the total amount you plan to allocate for trading. Position sizes will be calculated based on this. This is stored locally and never sent to our servers.">
            <div className="flex items-center gap-1">
              <span className="text-xs text-text-muted">₹</span>
              <input
                type="number"
                min={0}
                step={1000}
                value={tradingCapital || ''}
                onChange={(e) => { setTradingCapital(Number(e.target.value)); flash(); }}
                placeholder="e.g. 100000"
                className="w-32 bg-bg-secondary border border-border-default rounded-lg px-3 py-1.5 text-sm font-mono text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple"
              />
            </div>
          </SettingRow>

          <SettingRow label="Max Risk Per Trade" description="Maximum % of capital to risk on a single trade" tooltip="This controls position sizing. A 2% risk means if a trade hits its stop-loss, you lose at most 2% of your capital. Professional traders typically use 1-3%.">
            <div className="flex items-center gap-2">
              <input
                type="range"
                min={0.5}
                max={5}
                step={0.5}
                value={maxRiskPct}
                onChange={(e) => { setMaxRiskPct(Number(e.target.value)); flash(); }}
                className="w-24 accent-accent-purple"
                aria-label="Max risk per trade"
              />
              <span className="text-sm font-mono text-accent-purple w-12 text-right">{maxRiskPct}%</span>
            </div>
          </SettingRow>

          {tradingCapital > 0 && (
            <div className="bg-bg-secondary rounded-lg p-3 space-y-1">
              <p className="text-xs text-text-muted">Position sizing preview</p>
              <p className="text-sm text-text-primary">
                Max risk per trade: <span className="font-mono text-accent-purple">₹{(tradingCapital * maxRiskPct / 100).toLocaleString('en-IN')}</span>
              </p>
              <p className="text-xs text-text-muted">
                e.g. if stop-loss is 5% away → position size: <span className="font-mono text-text-secondary">₹{(tradingCapital * maxRiskPct / 100 / 0.05).toLocaleString('en-IN', { maximumFractionDigits: 0 })}</span>
              </p>
            </div>
          )}
        </section>

        {/* Notifications */}
        <section className="bg-bg-card border border-border-default rounded-xl p-5 space-y-4">
          <h2 className="text-base font-display font-semibold">🔔 Notifications</h2>

          {isNotificationSupported() && (
            <SettingRow label="Push Notifications" description="Desktop alerts for high-confidence signals" tooltip="When enabled, you'll get a desktop notification for new signals above your minimum confidence threshold. Works even when SignalFlow is in a background tab.">
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

        {/* Security — Password Change */}
        {session?.user && (
          <section className="bg-bg-card border border-border-default rounded-xl p-5 space-y-4">
            <h2 className="text-base font-display font-semibold">🔑 Security</h2>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-text-muted block mb-1">Current Password</label>
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  className="w-full sm:w-64 bg-bg-secondary border border-border-default rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent-purple"
                  autoComplete="current-password"
                />
              </div>
              <div>
                <label className="text-xs text-text-muted block mb-1">New Password</label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full sm:w-64 bg-bg-secondary border border-border-default rounded-lg px-3 py-2 text-sm text-text-primary focus:outline-none focus:border-accent-purple"
                  autoComplete="new-password"
                />
                <p className="text-[10px] text-text-muted mt-1">Min 8 chars, uppercase, lowercase, digit, special char</p>
              </div>
              <button
                onClick={handleChangePassword}
                disabled={!currentPassword || !newPassword}
                className="px-4 py-2 text-sm bg-accent-purple text-white rounded-lg hover:bg-accent-purple/90 transition-colors disabled:opacity-40"
              >
                Change Password
              </button>
              {passwordMsg && (
                <p className={`text-xs ${passwordMsg.type === 'success' ? 'text-signal-buy' : 'text-signal-sell'}`}>
                  {passwordMsg.text}
                </p>
              )}
            </div>
          </section>
        )}

        {/* Reset */}
        <section className="bg-bg-card border border-signal-sell/20 rounded-xl p-5 space-y-4">
          <h2 className="text-base font-display font-semibold text-signal-sell">⚠️ Danger Zone</h2>
          <div className="flex items-center justify-between">
            <p className="text-xs text-text-muted">Reset all settings to defaults</p>
            {!showResetConfirm ? (
              <button
                onClick={() => setShowResetConfirm(true)}
                className="px-3 py-1.5 text-xs rounded-lg border border-signal-sell/30 text-signal-sell hover:bg-signal-sell/10 transition-colors"
              >
                Reset to Defaults
              </button>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-xs text-signal-sell">Are you sure?</span>
                <button
                  onClick={() => { resetSettings(); setShowResetConfirm(false); }}
                  className="px-3 py-1.5 text-xs rounded-lg bg-signal-sell text-white hover:bg-signal-sell/80 transition-colors"
                >
                  Yes, Reset
                </button>
                <button
                  onClick={() => setShowResetConfirm(false)}
                  className="px-3 py-1.5 text-xs rounded-lg border border-border-default text-text-muted hover:text-text-primary transition-colors"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>

          {/* Account Deletion */}
          {session?.user && (
            <div className="pt-3 border-t border-signal-sell/10">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-text-muted">Permanently delete your account</p>
                  <p className="text-[10px] text-text-muted">All data (trades, alerts, watchlist) will be permanently removed.</p>
                </div>
                {!showDeleteConfirm ? (
                  <button
                    onClick={() => setShowDeleteConfirm(true)}
                    className="px-3 py-1.5 text-xs rounded-lg border border-signal-sell/30 text-signal-sell hover:bg-signal-sell/10 transition-colors"
                  >
                    Delete Account
                  </button>
                ) : (
                  <div className="flex flex-col items-end gap-2">
                    <input
                      type="password"
                      value={deletePassword}
                      onChange={(e) => setDeletePassword(e.target.value)}
                      placeholder="Enter password to confirm"
                      className="w-48 bg-bg-secondary border border-signal-sell/30 rounded-lg px-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-signal-sell"
                      autoComplete="current-password"
                    />
                    <div className="flex gap-2">
                      <button
                        onClick={handleDeleteAccount}
                        disabled={!deletePassword}
                        className="px-3 py-1.5 text-xs rounded-lg bg-signal-sell text-white hover:bg-signal-sell/80 transition-colors disabled:opacity-40"
                      >
                        Confirm Delete
                      </button>
                      <button
                        onClick={() => { setShowDeleteConfirm(false); setDeletePassword(''); setDeleteMsg(null); }}
                        className="px-3 py-1.5 text-xs rounded-lg border border-border-default text-text-muted hover:text-text-primary transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                    {deleteMsg && (
                      <p className="text-xs text-signal-sell">{deleteMsg.text}</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          )}
        </section>

        {/* App Info */}
        <div className="text-center text-xs text-text-muted space-y-1 pt-4">
          <p>SignalFlow AI v1.1.0</p>
          <p>AI-generated signals for educational purposes only. Not financial advice.</p>
          <Link href="/alerts" className="text-accent-purple hover:underline block mt-2">
            ⚙️ Configure alert preferences, watchlist & price alerts →
          </Link>
        </div>
      </div>
    </main>
  );
}

function SettingRow({ label, description, tooltip, children }: { label: string; description: string; tooltip?: string; children: React.ReactNode }) {
  const [showTip, setShowTip] = useState(false);
  return (
    <div className="flex items-center justify-between gap-4">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5">
          <p className="text-sm text-text-primary">{label}</p>
          {tooltip && (
            <div className="relative">
              <button
                type="button"
                onClick={() => setShowTip(!showTip)}
                onMouseEnter={() => setShowTip(true)}
                onMouseLeave={() => setShowTip(false)}
                className="text-text-muted hover:text-accent-purple transition-colors"
                aria-label={`Info about ${label}`}
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 16v-4M12 8h.01" />
                </svg>
              </button>
              {showTip && (
                <div className="absolute left-0 bottom-full mb-2 w-56 p-2.5 bg-bg-secondary border border-border-default rounded-lg shadow-lg text-xs text-text-secondary z-50">
                  {tooltip}
                </div>
              )}
            </div>
          )}
        </div>
        <p className="text-xs text-text-muted">{description}</p>
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  );
}
