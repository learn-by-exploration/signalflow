# JWT Algorithm and Token Storage — Architecture Decision Record

**Date**: 30 March 2026  
**Status**: Accepted  
**Context**: SignalFlow AI uses HS256 JWTs for authentication

## Decision: HS256 with Minimum Secret Length

We use **HS256** (HMAC-SHA256) for JWT signing with a minimum 32-character secret key enforced at startup.

### Why HS256 (not RS256)

- **Simpler ops**: Single secret vs key pair management
- **Performance**: Symmetric signing/verification is faster
- **Single service**: We don't have microservices that need to verify tokens independently

### Risks and Mitigations

| Risk | Mitigation | Status |
|------|-----------|--------|
| Secret key leak → all tokens forged | Min 32-char secret enforced at startup; stored in Railway secrets | ✅ Done |
| XSS can steal JWTs from session storage | CSP headers restrict script-src to 'self' | ✅ Done |
| JWTs in NextAuth session exposed to JS | Future: move to httpOnly cookies via Next.js API proxy | 🔜 Planned |

### Future: RS256 Migration

When we add:
- Mobile app clients
- Third-party integrations
- Microservice architecture

We should migrate to **RS256** (asymmetric). Steps:
1. Generate RSA-2048 key pair
2. Backend signs with private key
3. Other services verify with public key only
4. Support both RS256 and HS256 during transition period

### Future: httpOnly Cookie Token Storage

Currently, backend JWTs flow through NextAuth's session callback and are accessible
to client-side JavaScript. This is acceptable with strict CSP but not ideal.

**Safer approach** (planned):
1. Next.js API route `/api/auth/callback` receives JWT from backend
2. Stores it in an httpOnly, Secure, SameSite=Strict cookie
3. Frontend API calls go through Next.js API routes that attach the cookie server-side
4. No JWT ever touches client-side JavaScript

This requires refactoring the auth flow and is tracked for a future sprint.
