/**
 * FilterPanel — sidebar filters for graph exploration.
 */
'use client';

import { useGraphStore } from '@/store/graphStore';
import { ENTITY_TYPE_COLORS } from '@/lib/mkg-types';

const ENTITY_TYPES = ['Company', 'Facility', 'Country', 'Person', 'Sector', 'Product', 'Regulation', 'Event'];

const RELATION_TYPES = [
  'SUPPLIES_TO', 'COMPETES_WITH', 'SUBSIDIARY_OF', 'OPERATES_IN',
  'REGULATES', 'EMPLOYS', 'PRODUCES', 'DEPENDS_ON',
  'AFFECTS', 'OWNS', 'PARTNERS_WITH', 'INVESTS_IN',
  'ACQUIRES', 'LICENSES_FROM',
];

export function FilterPanel() {
  const { filters, setFilters, resetFilters } = useGraphStore();

  function toggleEntityType(type: string) {
    const current = filters.entityTypes;
    const next = current.includes(type)
      ? current.filter((t) => t !== type)
      : [...current, type];
    setFilters({ entityTypes: next });
  }

  function toggleRelationType(type: string) {
    const current = filters.relationTypes;
    const next = current.includes(type)
      ? current.filter((t) => t !== type)
      : [...current, type];
    setFilters({ relationTypes: next });
  }

  const hasFilters =
    filters.entityTypes.length > 0 ||
    filters.relationTypes.length > 0 ||
    filters.confidenceRange[0] > 0 ||
    filters.confidenceRange[1] < 1;

  return (
    <div className="rounded-xl border border-border-default bg-bg-secondary p-4 space-y-5">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-display font-semibold text-text-primary">Filters</h3>
        {hasFilters && (
          <button
            onClick={resetFilters}
            className="text-xs text-accent-purple hover:text-accent-purple/80"
          >
            Reset
          </button>
        )}
      </div>

      {/* Entity types */}
      <div>
        <h4 className="text-xs text-text-muted uppercase tracking-wider mb-2">Entity Types</h4>
        <div className="flex flex-wrap gap-1.5">
          {ENTITY_TYPES.map((type) => {
            const active = filters.entityTypes.includes(type);
            const color = ENTITY_TYPE_COLORS[type] || '#6B7280';
            return (
              <button
                key={type}
                onClick={() => toggleEntityType(type)}
                className={`px-2 py-1 text-xs rounded-md border transition-colors
                  ${active
                    ? 'border-transparent font-medium'
                    : 'border-border-default text-text-muted hover:border-border-hover'}`}
                style={active ? { backgroundColor: `${color}20`, color } : undefined}
              >
                {type}
              </button>
            );
          })}
        </div>
      </div>

      {/* Relation types */}
      <div>
        <h4 className="text-xs text-text-muted uppercase tracking-wider mb-2">Connection Types</h4>
        <div className="flex flex-wrap gap-1.5">
          {RELATION_TYPES.map((type) => {
            const active = filters.relationTypes.includes(type);
            return (
              <button
                key={type}
                onClick={() => toggleRelationType(type)}
                className={`px-2 py-1 text-xs rounded-md border transition-colors
                  ${active
                    ? 'bg-accent-purple/10 text-accent-purple border-accent-purple/30 font-medium'
                    : 'border-border-default text-text-muted hover:border-border-hover'}`}
              >
                {type.replace(/_/g, ' ')}
              </button>
            );
          })}
        </div>
      </div>

      {/* Confidence range */}
      <div>
        <h4 className="text-xs text-text-muted uppercase tracking-wider mb-2">
          Min Confidence: {Math.round(filters.confidenceRange[0] * 100)}%
        </h4>
        <input
          type="range"
          min={0}
          max={100}
          value={filters.confidenceRange[0] * 100}
          onChange={(e) =>
            setFilters({
              confidenceRange: [Number(e.target.value) / 100, filters.confidenceRange[1]],
            })
          }
          className="w-full accent-accent-purple"
        />
      </div>
    </div>
  );
}
