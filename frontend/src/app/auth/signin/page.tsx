'use client';

import { useState, Suspense } from 'react';
import { signIn } from 'next-auth/react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';

function SignInForm() {
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get('callbackUrl') ?? '/';
  const error = searchParams.get('error');

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [consented, setConsented] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);

  function fillDemo() {
    setEmail('demo@signalflow.ai');
    setPassword('demo123');
    setConsented(true);
  }

  async function handleCredentials(e: React.FormEvent) {
    e.preventDefault();
    if (!consented) return;
    setLoading(true);
    await signIn('credentials', { email, password, rememberMe: rememberMe ? 'true' : 'false', callbackUrl });
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
          <p className="text-sm text-text-secondary">Sign in to access your dashboard</p>
        </div>

        {error && (
          <div className="bg-signal-sell/10 border border-signal-sell/30 rounded-lg p-3 text-center">
            <p className="text-signal-sell text-sm">
              {error === 'CredentialsSignin'
                ? 'Invalid email or password'
                : 'An error occurred. Please try again.'}
            </p>
          </div>
        )}

        {/* Google */}
        <button
          onClick={() => consented && signIn('google', { callbackUrl })}
          disabled={!consented}
          className="w-full flex items-center justify-center gap-3 py-2.5 px-4 rounded-lg border border-border-default bg-bg-card hover:bg-bg-card-hover transition-colors text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg className="w-5 h-5" viewBox="0 0 24 24">
            <path
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
              fill="#4285F4"
            />
            <path
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              fill="#34A853"
            />
            <path
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              fill="#FBBC05"
            />
            <path
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              fill="#EA4335"
            />
          </svg>
          Continue with Google
        </button>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-border-default" />
          </div>
          <div className="relative flex justify-center text-xs">
            <span className="px-2 bg-bg-primary text-text-muted">or</span>
          </div>
        </div>

        {/* Credentials */}
        <form onSubmit={handleCredentials} className="space-y-4">
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
              className="w-full bg-bg-card border border-border-default rounded-lg px-3 py-2.5 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple"
              placeholder="••••••••"
            />
          </div>

          {/* Remember me */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={rememberMe}
              onChange={(e) => setRememberMe(e.target.checked)}
              className="rounded border-border-default bg-bg-card text-accent-purple focus:ring-accent-purple"
            />
            <span className="text-xs text-text-secondary">Remember me for 30 days</span>
          </label>

          <button
            type="submit"
            disabled={loading || !consented}
            className="w-full py-2.5 bg-accent-purple text-white text-sm rounded-lg font-medium hover:bg-accent-purple/90 transition-colors disabled:opacity-50"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        {/* Demo access */}
        <div className="bg-bg-card border border-border-default rounded-lg p-3 text-center space-y-2">
          <p className="text-xs text-text-muted">Want to try it out first?</p>
          <button
            onClick={fillDemo}
            className="text-sm text-accent-purple hover:underline font-medium"
          >
            Use Demo Account
          </button>
          <p className="text-[10px] text-text-muted font-mono">demo@signalflow.ai / demo123</p>
        </div>

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
      </div>
    </main>
  );
}

export default function SignInPage() {
  return (
    <Suspense fallback={
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-text-secondary text-sm">Loading...</div>
      </main>
    }>
      <SignInForm />
    </Suspense>
  );
}
