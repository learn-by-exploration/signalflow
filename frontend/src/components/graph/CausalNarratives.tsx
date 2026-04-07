/**
 * CausalNarratives — plain-English causal chain explanations.
 *
 * Renders AI-generated narratives from the CausalChainBuilder.
 */
'use client';

import Link from 'next/link';
import type { CausalChainItem } from '@/lib/mkg-types';
import { SEVERITY_COLORS } from '@/lib/mkg-types';

interface CausalNarrativesProps {
  chains: CausalChainItem[];
}

function severity(impact: number): keyof typeof SEVERITY_COLORS {
  if (impact >= 0.8) return 'critical';
  if (impact >= 0.6) return 'high';
  if (impact >= 0.3) return 'medium';
  return 'low';
}

export function CausalNarratives({ chains }: CausalNarrativesProps) {
  if (chains.length === 0) {
    return (
      <div className="text-center py-6 text-text-muted text-sm">
        No causal chains generated.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {chains.map((chain, i) => {
        const sev = severity(chain.impact_score);
        const color = SEVERITY_COLORS[sev];
        return (
          <div
            key={`${chain.affected_entity}-${i}`}
            className="rounded-lg border border-border-default bg-bg-secondary p-4"
          >
            {/* Path breadcrumb */}
            <div className="flex items-center gap-1.5 mb-2 flex-wrap">
              {chain.path.map((step, j) => (
                <span key={j} className="flex items-center gap-1.5">
                  <span className="text-xs text-text-secondary font-medium">{step}</span>
                  {j < chain.path.length - 1 && (
                    <span className="text-text-muted text-xs">
                      {chain.edge_labels?.[j] ? `→ ${chain.edge_labels[j].replace(/_/g, ' ')} →` : '→'}
                    </span>
                  )}
                </span>
              ))}
            </div>

            {/* Narrative */}
            <p className="text-sm text-text-primary leading-relaxed mb-2">
              {chain.narrative}
            </p>

            {/* Footer */}
            <div className="flex items-center gap-3 text-xs">
              <span className="font-mono" style={{ color }}>
                Impact: {Math.round(chain.impact_score * 100)}%
              </span>
              <span className="text-text-muted">
                {chain.hops} hop{chain.hops !== 1 ? 's' : ''}
              </span>
              <Link
                href={`/knowledge-graph/entity/${chain.affected_entity}`}
                className="text-accent-purple hover:text-accent-purple/80 ml-auto"
              >
                View {chain.affected_name} →
              </Link>
            </div>
          </div>
        );
      })}
    </div>
  );
}
