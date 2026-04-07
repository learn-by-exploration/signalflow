/**
 * ProvenanceBadge — shows origin of an edge or entity.
 *
 * Infers provenance from the edge `source` field:
 * - null/undefined → Seed data (curated)
 * - Contains "claude" or "extraction" → AI-extracted
 * - Contains article/news source name → News-sourced
 * - Otherwise → Unknown
 */
'use client';

export type ProvenanceType = 'seed' | 'ai' | 'news' | 'unknown';

export function inferProvenance(source: string | null | undefined): ProvenanceType {
  if (!source) return 'seed';
  const s = source.toLowerCase();
  if (s.includes('claude') || s.includes('extraction') || s.includes('ai') || s.includes('llm'))
    return 'ai';
  if (
    s.includes('reuters') ||
    s.includes('bloomberg') ||
    s.includes('article') ||
    s.includes('news') ||
    s.includes('rss')
  )
    return 'news';
  return 'unknown';
}

const PROVENANCE_CONFIG: Record<ProvenanceType, { emoji: string; label: string; color: string }> =
  {
    seed: { emoji: '🌱', label: 'Curated', color: '#22C55E' },
    ai: { emoji: '🤖', label: 'AI-Extracted', color: '#818CF8' },
    news: { emoji: '📰', label: 'News-Sourced', color: '#F59E0B' },
    unknown: { emoji: '❓', label: 'Unknown', color: '#6B7280' },
  };

interface ProvenanceBadgeProps {
  source?: string | null;
  size?: 'sm' | 'md';
  showLabel?: boolean;
}

export function ProvenanceBadge({ source, size = 'sm', showLabel = false }: ProvenanceBadgeProps) {
  const prov = inferProvenance(source);
  const cfg = PROVENANCE_CONFIG[prov];

  const textSize = size === 'sm' ? 'text-[10px]' : 'text-xs';

  return (
    <span
      className={`inline-flex items-center gap-0.5 ${textSize} rounded-full font-mono`}
      style={{ backgroundColor: `${cfg.color}15`, color: cfg.color }}
      title={`${cfg.label} — source: ${source || 'seed data'}`}
    >
      <span className={size === 'sm' ? 'text-xs' : 'text-sm'}>{cfg.emoji}</span>
      {showLabel && <span className="px-1">{cfg.label}</span>}
    </span>
  );
}
