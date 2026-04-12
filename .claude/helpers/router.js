#!/usr/bin/env node
/**
 * SignalFlow Task Router
 * Detects task domains from the user prompt and maps to the right agent(s).
 * Uses a two-tier system:
 *   - Project agents (signalflow-*): know the codebase architecture
 *   - Specialist agents (ecc-*, ws-*, sc-*): deep domain expertise
 * Multi-domain prompts → parallel-dispatch.
 */

const DOMAINS = [
  // ══════════════════════════════════════════════════════════════
  // IMPLEMENTATION DOMAINS — project agent + specialist pair
  // ══════════════════════════════════════════════════════════════

  // AI Engine / Claude API / LLM pipeline
  { pattern: /sentiment|ai.engine|claude|anthropic|llm|cost.tracker|budget|token|briefing|news.fetch|finbert|sanitiz|dedup|event.chain|prompt\b|reasoner/i,
    agents: ['signalflow-ai-engine', 'ws-llm-application-dev-ai-engineer'],
    label: 'ai-engine', impl: true },

  // Signal generation pipeline
  { pattern: /signal.gen|scorer|target.price|stop.loss|confidence|calibrat|mtf.confirm|risk.guard|shadow.mode|streak|signal_type|STRONG_BUY|STRONG_SELL|risk.reward/i,
    agents: ['signalflow-signal', 'ws-backend-development-tdd-orchestrator'],
    label: 'signal-pipeline', impl: true },

  // Technical analysis / indicators
  { pattern: /indicator|rsi|macd|bollinger|sma|ema|atr\b|volume.signal|TechnicalAnalyzer|technical.anal/i,
    agents: ['signalflow-data', 'ws-python-development-python-pro'],
    label: 'technical-analysis', impl: true },

  // Data ingestion / market fetchers
  { pattern: /ingest|yfinance|binance|alpha.vantage|market.data|ohlcv|market.hours|nse|bse|forex.rate|crypto.*price|websocket.*market/i,
    agents: ['signalflow-data', 'ws-python-development-fastapi-pro'],
    label: 'data-ingestion', impl: true },

  // FastAPI endpoints / REST / WebSocket
  { pattern: /fastapi|endpoint|router\b|api\/v1|pydantic|schema.*response|response.*schema|rate.limit|cors|websocket.*endpoint/i,
    agents: ['signalflow-backend', 'ws-api-scaffolding-fastapi-pro'],
    label: 'api-backend', impl: true },

  // Celery / background tasks / scheduler
  { pattern: /celery|beat.schedule|periodic.task|crontab|task.*worker|background.job|task.*async|async.*task/i,
    agents: ['signalflow-backend', 'ws-python-development-python-pro'],
    label: 'celery-tasks', impl: true },

  // PostgreSQL / TimescaleDB / SQLAlchemy / migrations
  { pattern: /postgres|timescale|alembic|migration\b|hypertable|sqlalchemy|orm.model|decimal.*price|timestamptz/i,
    agents: ['signalflow-backend', 'ws-database-design-sql-pro', 'ws-database-migrations-database-admin'],
    label: 'database', impl: true },

  // Redis / caching / pubsub
  { pattern: /redis|cache\b|cach(e|ing)|pubsub|pub.sub|cache.*expire|cache.*key/i,
    agents: ['signalflow-backend', 'ws-python-development-python-pro'],
    label: 'redis-cache', impl: true },

  // Auth / JWT / payments / Razorpay
  { pattern: /auth\b|jwt|refresh.token|login\b|register\b|password|razorpay|subscription|payment|webhook.*payment|tier.gat/i,
    agents: ['signalflow-security', 'ecc-security-reviewer'],
    label: 'auth-payments', impl: true },

  // Telegram bot / alerts / dispatch
  { pattern: /telegram|bot.command|alert.dispatch|formatter\b|morning.brief|evening.wrap|weekly.digest/i,
    agents: ['signalflow-backend', 'ws-python-development-python-pro'],
    label: 'alerts-telegram', impl: true },

  // MKG — Market Knowledge Graph
  { pattern: /mkg\b|knowledge.graph|entity.service|graph.storage|seed.loader|event.entity|causal.link|graph.canvas|entity.card|entity.drawer|entity.search|entity.lineage|impact.simulat|supply.chain|provenance|graph.stats/i,
    agents: ['signalflow-backend', 'ws-backend-development-backend-architect'],
    label: 'mkg', impl: true },

  // Frontend / Next.js / React / Tailwind
  { pattern: /next\.js|nextjs|react.component|\.tsx\b|frontend|tailwind|zustand|useSignals|useMKG|dashboard.*page|recharts|dark.theme|signal.card|market.overview/i,
    agents: ['signalflow-frontend', 'ecc-typescript-reviewer'],
    label: 'frontend', impl: true },

  // SEO
  { pattern: /seo\b|slug\b|sitemap|meta.tag|seo.page|seo.task/i,
    agents: ['signalflow-backend', 'ecc-seo-specialist'],
    label: 'seo', impl: true },

  // DevOps / Docker / Railway / deploy
  { pattern: /docker.compose|dockerfile|railway\b|supervisord|ci.cd|github.action|deploy\b/i,
    agents: ['ws-cicd-automation-deployment-engineer', 'ws-cicd-automation-devops-troubleshooter'],
    label: 'devops', impl: false },

  // ══════════════════════════════════════════════════════════════
  // QUALITY & PROCESS DOMAINS — specialist agents only
  // ══════════════════════════════════════════════════════════════

  // TDD / test writing
  { pattern: /\btest\b|pytest|vitest|coverage|fixture|conftest|mock\b|unit.test|integration.test|write.*test|test.*first|tdd|red.green/i,
    agents: ['ecc-tdd-guide', 'ws-backend-development-tdd-orchestrator', 'ws-python-development-python-pro'],
    label: 'testing', impl: false },

  // Code review (explicit ask)
  { pattern: /review\b|code.quality|code.smell|lgtm|pr.review|pull.request/i,
    agents: ['ecc-code-reviewer', 'ecc-python-reviewer', 'superpowers-code-reviewer'],
    label: 'review', impl: false },

  // Security audit / OWASP
  { pattern: /security.audit|owasp|penetrat|vulnerab|injection|xss\b|csrf\b|secret.*leak|hardcode.*key/i,
    agents: ['ecc-security-reviewer', 'gsd-security-auditor', 'ws-security-scanning-security-auditor'],
    label: 'security-audit', impl: false },

  // Performance / profiling
  { pattern: /performance|bottleneck|slow.query|n\+1|latency|profil|optimize.*query|cache.hit|memory.leak/i,
    agents: ['ecc-performance-optimizer', 'ws-backend-development-performance-engineer', 'ws-database-cloud-optimization-database-optimizer'],
    label: 'performance', impl: false },

  // Refactor / cleanup
  { pattern: /refactor|dead.code|clean.up|simplif|extract.*function|dry\b|yagni|technical.debt/i,
    agents: ['ecc-refactor-cleaner', 'sc-refactoring-expert'],
    label: 'refactor', impl: false },

  // Debugging / errors
  { pattern: /debug\b|traceback|exception\b|stack.trace|error.*500|500.*error|crash\b|fix.bug|reproduce/i,
    agents: ['gsd-debugger', 'ws-error-debugging-error-detective'],
    label: 'debug', impl: false },

  // Build / import errors
  { pattern: /build.error|import.error|module.not.found|cannot.import|compile.error|type.error.*python/i,
    agents: ['ecc-build-error-resolver', 'ws-error-diagnostics-error-detective'],
    label: 'build-fix', impl: false },

  // Observability / logging / metrics / Prometheus
  { pattern: /observ|prometheus|metric\b|logging|structlog|sentry|trace\b|slo\b|sli\b|monitor/i,
    agents: ['ws-observability-monitoring-observability-engineer', 'ws-python-development-python-pro'],
    label: 'observability', impl: false },

  // Architecture / planning
  { pattern: /architect\b|design.*decision|adr\b|trade.?off|plan.*feature|system.design/i,
    agents: ['ecc-architect', 'sc-system-architect'],
    label: 'architecture', impl: false },

  // Docs
  { pattern: /docstring|readme|changelog|api.doc|write.*doc/i,
    agents: ['ecc-doc-updater', 'ws-documentation-generation-api-documenter'],
    label: 'docs', impl: false },
];

function routeTask(task) {
  if (!task || !task.trim()) {
    return { agents: [], domains: [], action: 'handle-directly' };
  }

  const matched = [];
  const seenAgents = new Set();

  for (const d of DOMAINS) {
    if (d.pattern.test(task)) {
      const newAgents = d.agents.filter(a => !seenAgents.has(a));
      if (newAgents.length > 0) {
        newAgents.forEach(a => seenAgents.add(a));
        matched.push({ agents: newAgents, domain: d.label, impl: d.impl });
      }
    }
  }

  if (matched.length === 0) {
    return { agents: [], domains: [], action: 'handle-directly',
      note: 'No specific domain matched — handle directly' };
  }

  // Cap at 4 agents max — beyond that Claude picks the most relevant anyway
  const allAgents = matched.flatMap(m => m.agents).slice(0, 4);
  const allDomains = matched.map(m => m.domain);
  const hasImpl = matched.some(m => m.impl);

  return {
    agents: allAgents,
    domains: allDomains,
    action: allAgents.length > 1 ? 'parallel-dispatch' : 'dispatch',
    review: hasImpl,
  };
}

if (require.main === module) {
  const task = process.argv.slice(2).join(' ');
  if (task) console.log(JSON.stringify(routeTask(task), null, 2));
}

module.exports = { routeTask, DOMAINS };
