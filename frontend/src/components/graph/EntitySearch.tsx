/**
 * EntitySearch — fuzzy search for MKG entities with autocomplete dropdown.
 */
'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { mkgApi } from '@/lib/mkg-api';
import { useGraphStore } from '@/store/graphStore';
import type { MKGEntity } from '@/lib/mkg-types';
import { ENTITY_TYPE_COLORS } from '@/lib/mkg-types';

interface EntitySearchProps {
  onSelect?: (entity: MKGEntity) => void;
  placeholder?: string;
}

export function EntitySearch({
  onSelect,
  placeholder = 'Search companies, facilities, countries...',
}: EntitySearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<MKGEntity[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  const { setSearchQuery } = useGraphStore();

  const doSearch = useCallback(async (q: string) => {
    if (q.length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }
    setIsLoading(true);
    try {
      const data = await mkgApi.searchEntities(q, undefined, 10);
      setResults(data);
      setIsOpen(data.length > 0);
    } catch {
      setResults([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  function handleChange(value: string) {
    setQuery(value);
    setSearchQuery(value);
    setActiveIndex(-1);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => doSearch(value), 300);
  }

  function handleSelect(entity: MKGEntity) {
    setQuery(entity.name);
    setIsOpen(false);
    setActiveIndex(-1);
    onSelect?.(entity);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!isOpen) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex((i) => Math.max(i - 1, 0));
    } else if (e.key === 'Enter' && activeIndex >= 0) {
      e.preventDefault();
      handleSelect(results[activeIndex]);
    } else if (e.key === 'Escape') {
      setIsOpen(false);
    }
  }

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={wrapperRef} className="relative w-full">
      <div className="relative">
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => handleChange(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => results.length > 0 && setIsOpen(true)}
          placeholder={placeholder}
          className="w-full px-4 py-3 rounded-lg bg-bg-secondary border border-border-default
                     text-text-primary placeholder-text-muted
                     focus:outline-none focus:border-accent-purple focus:ring-1 focus:ring-accent-purple
                     font-body text-sm"
          role="combobox"
          aria-expanded={isOpen}
          aria-autocomplete="list"
          aria-controls="entity-search-results"
          aria-activedescendant={activeIndex >= 0 ? `entity-option-${activeIndex}` : undefined}
        />
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <div className="w-4 h-4 border-2 border-accent-purple border-t-transparent rounded-full animate-spin" />
          </div>
        )}
      </div>

      {isOpen && results.length > 0 && (
        <ul
          id="entity-search-results"
          role="listbox"
          className="absolute z-50 mt-1 w-full rounded-lg border border-border-default
                     bg-bg-secondary shadow-xl max-h-72 overflow-auto"
        >
          {results.map((entity, i) => (
            <li
              key={entity.id}
              id={`entity-option-${i}`}
              role="option"
              aria-selected={i === activeIndex}
              onClick={() => handleSelect(entity)}
              onMouseEnter={() => setActiveIndex(i)}
              className={`px-4 py-3 cursor-pointer flex items-center gap-3 text-sm
                ${i === activeIndex ? 'bg-accent-purple/10' : 'hover:bg-white/5'}`}
            >
              <span
                className="w-2 h-2 rounded-full shrink-0"
                style={{ backgroundColor: ENTITY_TYPE_COLORS[entity.entity_type] || '#6B7280' }}
              />
              <div className="flex-1 min-w-0">
                <span className="text-text-primary truncate block">{entity.name}</span>
                <span className="text-text-muted text-xs">{entity.entity_type}</span>
              </div>
              {entity.tags?.length > 0 && (
                <div className="flex gap-1 shrink-0">
                  {entity.tags.slice(0, 2).map((tag) => (
                    <span
                      key={tag}
                      className="px-1.5 py-0.5 text-[10px] rounded bg-white/5 text-text-muted"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
