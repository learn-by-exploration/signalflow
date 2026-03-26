'use client';

import { useState, Suspense } from 'react';
import { signIn } from 'next-auth/react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { API_URL } from '@/lib/constants';

function SignUpForm() {
  const searchParams = useSearchParams();
  const rawCallback = searchParams.get('callbackUrl') ?? '/';
  const callbackUrl = rawCallback.startsWith('/') && !rawCallback.startsWith('//') ? rawCallback : '/';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [consented, setConsented] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!consented) return;
    setError(null);

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/v1/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => null);
        const detail = body?.detail ?? `Registration failed (${res.status})`;
        setError(detail);
        setLoading(false);
        return;
      }

      // Registration successful — sign in automatically
      await signIn('credentials', { email, password, callbackUrl });
    } catch {
      setError('Network error. Please try again.');
    }

    setLoading(false);
  }

  return (
    <main className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm space-y-6">
        {/* Logo / Branding */}
        <div className="text-center space-y-2">
          <h1 className="text-2xl font-display font-bold">
            <span className="text-accent-purple">Signal</span>Flow AI
          </h1>
          <p className="text-sm text-text-secondary">Create your account</p>
        </div>

        {error && (
          <div className="bg-signal-sell/10 border border-signal-sell/30 rounded-lg p-3 text-center">
            <p className="text-signal-sell text-sm">{error}</p>
          </div>
        )}

        {/* Credentials */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="text-xs text-text-secondary block mb-1">
              Email
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
          <div>
            <label htmlFor="password" className="text-xs text-text-secondary block mb-1">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full bg-bg-card border border-border-default rounded-lg px-3 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple"
              placeholder="Min. 8 characters"
            />
          </div>
          <div>
            <label htmlFor="confirmPassword" className="text-xs text-text-secondary block mb-1">
              Confirm Password
            </label>
            <input
              id="confirmPassword"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              minLength={8}
              className="w-full bg-bg-card border border-border-default rounded-lg px-3 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple"
              placeholder="Re-enter password"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !consented}
            className="w-full py-2.5 bg-accent-purple text-white text-sm rounded-lg font-medium hover:bg-accent-purple/90 transition-colors disabled:opacity-50"
          >
            {loading ? 'Creating account...' : 'Create Account'}
          </button>
        </form>

        {/* Consent checkbox */}
        <label className="flex items-start gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={consented}
            onChange={(e) => setConsented(e.target.checked)}
            className="mt-1 rounded border-border-default bg-bg-card text-accent-purple focus:ring-accent-purple"
          />
          <span className="text-xs text-text-secondary leading-relaxed">
            I am 18 years or older. I have read and agree to the{' '}
            <Link
              href="/terms"
              target="_blank"
              className="text-accent-purple underline"
              onClick={(e) => e.stopPropagation()}
            >
              Terms of Service
            </Link>{' '}
            and{' '}
            <Link
              href="/privacy"
              target="_blank"
              className="text-accent-purple underline"
              onClick={(e) => e.stopPropagation()}
            >
              Privacy Policy
            </Link>
            . I understand that SignalFlow AI provides AI-generated analysis for educational
            purposes only and does not constitute investment advice.
          </span>
        </label>

        {/* Sign In link */}
        <p className="text-center text-sm text-text-secondary">
          Already have an account?{' '}
          <Link href="/auth/signin" className="text-accent-purple hover:underline font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </main>
  );
}

export default function SignUpPage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-text-secondary text-sm">Loading...</div>
      </main>
    }>
      <SignUpForm />
    </Suspense>
  );
}
