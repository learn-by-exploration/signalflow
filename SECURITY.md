# Security Policy — SignalFlow AI

## Reporting a Vulnerability

If you discover a security vulnerability in SignalFlow AI, please report it responsibly.

### How to Report
- **Email**: Send details to the repository owner (do not open a public issue)
- **Include**: Description of the vulnerability, steps to reproduce, potential impact, and suggested fix if you have one

### What to Expect
- Acknowledgment within 48 hours
- Assessment and severity classification within 5 business days
- Fix timeline communicated based on severity

### Severity Levels
| Level | Response Time | Examples |
|-------|--------------|---------|
| **Critical** | 24 hours | Auth bypass, data exposure, RCE |
| **High** | 3 days | Privilege escalation, injection, CSRF |
| **Medium** | 1 week | Information leak, missing rate limits |
| **Low** | 2 weeks | Minor misconfiguration, verbose errors |

---

## Security Measures in Place

### Authentication & Authorization
- JWT-based authentication with refresh token rotation
- bcrypt password hashing with salt
- Tier-based access control (free/pro/admin)
- API key authentication for service-to-service calls
- WebSocket authentication required for real-time feeds

### Data Protection
- All prices stored as `Decimal`, never `float`
- SQL injection prevention via SQLAlchemy ORM (parameterized queries)
- Input validation on all endpoints (Pydantic v2 schemas)
- CORS restricted to configured frontend origin
- Rate limiting on API endpoints (SlowAPI)

### AI Security
- Prompt injection prevention on Claude API calls
- AI cost budget enforcement ($30/month cap)
- Input sanitization before AI prompt construction

### Infrastructure
- HTTPS/TLS in production
- Environment variables for all secrets (never hardcoded)
- Structured logging (no secrets in logs)
- Sentry error tracking with PII scrubbing

---

## Scope

### In Scope
- SignalFlow AI backend (FastAPI application)
- SignalFlow AI frontend (Next.js application)
- Database schema and queries
- Authentication and authorization logic
- API endpoints and WebSocket handlers
- Celery task security
- Telegram bot message handling

### Out of Scope
- Third-party services (Binance, yfinance, Alpha Vantage, Claude API)
- Infrastructure provider (Railway) vulnerabilities
- Social engineering attacks
- Denial of service attacks on infrastructure

---

## Security Audit History

| Date | Type | Findings | Status |
|------|------|----------|--------|
| Mar 2026 | Automated security hackathon (300 agents) | 147 vulnerabilities, 23 critical | Sprints 0-4 remediated |
| Mar 2026 | Security Sprint 0 — Emergency fixes | 7 critical vulns fixed | Complete |
| Mar 2026 | Security Sprint 1 — Auth hardening | JWT, access control, WebSocket auth | Complete |
| Mar 2026 | Security Sprint 2 — Data integrity | Race conditions, financial precision | Complete |
| Mar 2026 | Security Sprint 3 — AI security | Prompt injection, DoS protection | Complete |
| Mar 2026 | Security Sprint 4 — Monitoring | Structured logging, hardening | Complete |

See [docs/security/](docs/security/) for detailed reports.
