import type { NextAuthOptions } from 'next-auth';
import GoogleProvider from 'next-auth/providers/google';
import CredentialsProvider from 'next-auth/providers/credentials';

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID ?? '',
      clientSecret: process.env.GOOGLE_CLIENT_SECRET ?? '',
    }),
    CredentialsProvider({
      name: 'Email',
      credentials: {
        email: { label: 'Email', type: 'email', placeholder: 'you@example.com' },
        password: { label: 'Password', type: 'password' },
        rememberMe: { label: 'Remember me', type: 'text' },
      },
      async authorize(credentials) {
        const email = credentials?.email;
        const password = credentials?.password;

        // Admin user
        if (
          email === process.env.ADMIN_EMAIL &&
          password === process.env.ADMIN_PASSWORD
        ) {
          return { id: '1', email: email ?? '', name: 'Admin' };
        }

        // Demo user — allows anyone to try the platform
        if (
          email === (process.env.DEMO_EMAIL ?? 'demo@signalflow.ai') &&
          password === (process.env.DEMO_PASSWORD ?? 'demo123')
        ) {
          return { id: '2', email: email ?? '', name: 'Demo User' };
        }

        return null;
      },
    }),
  ],
  pages: {
    signIn: '/auth/signin',
  },
  session: {
    strategy: 'jwt',
    maxAge: 7 * 24 * 60 * 60, // 7 days
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id = user.id;
        token.iat = Math.floor(Date.now() / 1000);
      }
      // Rotate token if older than 1 day
      const tokenAge = Math.floor(Date.now() / 1000) - ((token.iat as number) || 0);
      if (tokenAge > 86400) {
        token.iat = Math.floor(Date.now() / 1000);
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        (session.user as { id?: string }).id = token.id as string;
      }
      return session;
    },
  },
  secret: process.env.NEXTAUTH_SECRET,
};
