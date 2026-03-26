# SignalFlow AI — Documentation Index

> Navigate all project documentation from here.

---

## Quick Links

| I need to... | Read this |
|-------------|-----------|
| Set up the project | [README.md](../README.md) |
| Understand the architecture | [CLAUDE.md](../CLAUDE.md) |
| See what changed | [CHANGELOG.md](../CHANGELOG.md) |
| Use the API | [reference/api.md](reference/api.md) |
| Deploy to production | [guides/deployment.md](guides/deployment.md) |
| Handle an incident | [operations/runbook.md](operations/runbook.md) |
| Contribute code | [CONTRIBUTING.md](../CONTRIBUTING.md) |
| Report a vulnerability | [SECURITY.md](../SECURITY.md) |

---

## Documentation Map

### Reference (Technical Truth)
Authoritative specs. Change when code changes.

| File | Audience | Description |
|------|----------|-------------|
| [api.md](reference/api.md) | Developer | All 35+ REST endpoints + WebSocket protocol |
| [database-schema.md](reference/database-schema.md) | Developer | All 17 tables, columns, indexes, relationships |
| [environment-variables.md](reference/environment-variables.md) | Developer, Ops | All env vars with descriptions and defaults |

### Guides (How-To)
Step-by-step instructions for humans.

| File | Audience | Description |
|------|----------|-------------|
| [quickstart.md](guides/quickstart.md) | Developer | 5-minute setup with Docker |
| [development.md](guides/development.md) | Developer | Daily workflow, testing, linting |
| [deployment.md](guides/deployment.md) | DevOps | Railway deployment runbook |
| [troubleshooting.md](guides/troubleshooting.md) | Developer | Common errors and fixes |

### Operations (Production)
Runbooks for when things are running (or broken).

| File | Audience | Description |
|------|----------|-------------|
| [runbook.md](operations/runbook.md) | Ops | Incident response procedures |
| [monitoring.md](operations/monitoring.md) | Ops | Sentry, Celery, uptime setup |
| [backup-recovery.md](operations/backup-recovery.md) | Ops | Database backup and restore |

### Decisions (Why We Built It This Way)
Architecture Decision Records — historical context.

| File | Decision |
|------|----------|
| [001-fastapi-over-django.md](decisions/001-fastapi-over-django.md) | Why FastAPI for the backend |
| [002-zustand-over-redux.md](decisions/002-zustand-over-redux.md) | Why Zustand for state management |
| [003-claude-sonnet-model.md](decisions/003-claude-sonnet-model.md) | Why Claude Sonnet for AI |
| [004-timescaledb-for-ohlcv.md](decisions/004-timescaledb-for-ohlcv.md) | Why TimescaleDB for market data |

### Sprints (Historical)
Planning and execution records for each development phase.

| File | Phase | Status |
|------|-------|--------|
| [sprint-01-foundation.md](sprints/sprint-01-foundation.md) | Sprint 1-4 improvements | Shipped ✅ |
| [sprint-02-improvements.md](sprints/sprint-02-improvements.md) | Sprint 5 critical fixes | Shipped ✅ |
| [sprint-03-robustness.md](sprints/sprint-03-robustness.md) | Sprint 7-9 robustness | Shipped ✅ |
| [sprint-04-polish.md](sprints/sprint-04-polish.md) | Sprint 10+ polish | Partially shipped |
| [v1.1-action-plan.md](sprints/v1.1-action-plan.md) | v1.1 expert review fixes | Shipped ✅ |
| [v1.2-review-and-docs-plan.md](sprints/v1.2-review-and-docs-plan.md) | v1.2 review + docs plan | In progress |

### Reviews (Expert Feedback)
Multi-perspective assessments from simulated expert panels.

| File | Panel Size | Key Finding |
|------|-----------|-------------|
| [v0.0.1-ui-review.md](reviews/v0.0.1-ui-review.md) | 20 reviewers | Score 7.2/10; needs guided onboarding |
| [v1.0-next-features-review.md](reviews/v1.0-next-features-review.md) | 25 reviewers | Feature roadmap and revenue model |
| [multi-agent-review.md](reviews/multi-agent-review.md) | 4 perspectives | MVP 85% complete assessment |

### Research (Future Features)
Concepts explored but not yet built. Reference for future sprints.

| File | Feature | Status |
|------|---------|--------|
| [causal-event-chains.md](research/causal-event-chains.md) | Event knowledge graph | Partially built |
| [event-chain-reasoning.md](research/event-chain-reasoning.md) | IB-style causal reasoning | Research |
| [news-intelligence.md](research/news-intelligence.md) | Event taxonomy system | Research |
| [neural-trader-news.md](research/neural-trader-news.md) | Advanced news dashboard | Research |

### Security
Security assessments and remediation plans.

| File | Description | Status |
|------|-------------|--------|
| [hackathon-report.md](security/hackathon-report.md) | 147 vulnerabilities found | Sprints 0-4 fixed |
| [remediation-plan.md](security/remediation-plan.md) | 5-sprint fix roadmap | Sprints 0-4 complete |
| [hardening-plan.md](security/hardening-plan.md) | 6-phase hardening plan | Phases 0-6 done |

### Compliance
Legal, regulatory, and data protection.

| File | Description | Status |
|------|-------------|--------|
| [regulatory-spec.md](compliance/regulatory-spec.md) | SEBI/DPDPA/RBI gaps | Assessment complete |
| [regulatory-plan.md](compliance/regulatory-plan.md) | 4-sprint compliance roadmap | Not started |
| [data-breach-template.md](compliance/data-breach-template.md) | Incident response template | Ready |
