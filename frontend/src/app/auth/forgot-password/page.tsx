'use client';

import { useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';

type Step = 'request' | 'reset' | 'done';

export default function ForgotPasswordPage() {
  const [step, setStep] = useState<Step>('request');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleRequest(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.forgotPassword(email);
      setStep('reset');
    } catch {
      setError('Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  async function handleReset(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters.');
      return;
    }
    setLoading(true);
    try {
      await api.resetPassword({ email, code, new_password: newPassword });
      setStep('done');
    } catch (err: unknown) {
      const detail = (err as { detail?: string })?.detail;
      setError(detail ?? 'Invalid or expired code. Please try again.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-display font-bold">
            <span className="text-accent-purple">Signal</span>Flow AI
          </h1>
          <p className="text-sm text-text-secondary">
            {step === 'request' && 'Reset your password'}
            {step === 'reset' && 'Enter your reset code'}
            {step === 'done' && 'Password updated'}
          </p>
        </div>

        {error && (
          <div className="bg-signal-sell/10 border border-signal-sell/30 rounded-lg p-3 text-center">
            <p className="text-signal-sell text-sm">{error}</p>
          </div>
        )}

        {step === 'request' && (
          <form onSubmit={handleRequest} className="space-y-4">
            <div>
              <label htmlFor="email" className="text-xs text-text-secondary block mb-1">
                Email address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full bg-bg-card border border-border-default rounded-lg px-3 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple"
                placeholder="you@example.com"
              />
            </div>
            <p className="text-xs text-text-muted">
              We&apos;ll send a 6-digit reset code to your email address.
            </p>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-accent-purple text-white text-sm rounded-lg font-medium hover:bg-accent-purple/90 transition-colors disabled:opacity-50"
            >
              {loading ? 'Sending…' : 'Send Reset Code'}
            </button>
          </form>
        )}

        {step === 'reset' && (
          <form onSubmit={handleReset} className="space-y-4">
            <div className="bg-bg-card border border-border-default rounded-lg p-3 text-xs text-text-muted">
              A 6-digit code was sent to <span className="text-text-primary font-medium">{email}</span>. Check your email and enter it below.
            </div>
            <div>
              <label htmlFor="code" className="text-xs text-text-secondary block mb-1">
                Reset code
              </label>
              <input
                id="code"
                type="text"
                inputMode="numeric"
                maxLength={6}
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                required
                className="w-full bg-bg-card border border-border-default rounded-lg px-3 py-2.5 text-sm font-mono text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple tracking-widest"
                placeholder="123456"
              />
            </div>
            <div>
              <label htmlFor="new-password" className="text-xs text-text-secondary block mb-1">
                New password
              </label>
              <input
                id="new-password"
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={8}
                className="w-full bg-bg-card border border-border-default rounded-lg px-3 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple"
                placeholder="Min. 8 characters"
              />
            </div>
            <div>
              <label htmlFor="confirm-password" className="text-xs text-text-secondary block mb-1">
                Confirm new password
              </label>
              <input
                id="confirm-password"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="w-full bg-bg-card border border-border-default rounded-lg px-3 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple"
                placeholder="••••••••"
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 bg-accent-purple text-white text-sm rounded-lg font-medium hover:bg-accent-purple/90 transition-colors disabled:opacity-50"
            >
              {loading ? 'Updating…' : 'Update Password'}
            </button>
            <button
              type="button"
              onClick={() => setStep('request')}
              className="w-full text-xs text-text-muted hover:text-text-secondary transition-colors"
            >
              Didn&apos;t receive a code? Send again
            </button>
          </form>
        )}

        {step === 'done' && (
          <div className="text-center space-y-4">
            <p className="text-4xl">✅</p>
            <p className="text-sm text-text-secondary">
              Your password has been updated successfully.
            </p>
            <Link
              href="/auth/signin"
              className="block w-full py-2.5 bg-accent-purple text-white text-sm rounded-lg font-medium hover:bg-accent-purple/90 transition-colors text-center"
            >
              Sign In
            </Link>
          </div>
        )}

        <p className="text-center text-sm text-text-secondary">
          <Link href="/auth/signin" className="text-accent-purple hover:underline">
            ← Back to Sign In
          </Link>
        </p>
      </div>
    </main>
  );
}
