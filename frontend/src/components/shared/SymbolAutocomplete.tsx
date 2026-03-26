'use client';

import { useState, useRef, useEffect } from 'react';

const TRACKED_SYMBOLS = {
  stock: [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ITC.NS',
    'ICICIBANK.NS', 'KOTAKBANK.NS', 'LT.NS', 'SBIN.NS', 'BHARTIARTL.NS',
    'AXISBANK.NS', 'WIPRO.NS', 'HCLTECH.NS', 'MARUTI.NS', 'TATAMOTORS.NS',
  ],
  crypto: [
    'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT',
    'ADAUSDT', 'DOGEUSDT', 'DOTUSDT', 'AVAXUSDT', 'POLUSDT',
  ],
  forex: [
    'USD/INR', 'EUR/USD', 'GBP/JPY', 'GBP/USD', 'USD/JPY', 'AUD/USD',
  ],
};

const ALL_SYMBOLS = [
  ...TRACKED_SYMBOLS.stock,
  ...TRACKED_SYMBOLS.crypto,
  ...TRACKED_SYMBOLS.forex,
];

interface SymbolAutocompleteProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit?: () => void;
  placeholder?: string;
  className?: string;
}

export function SymbolAutocomplete({ value, onChange, onSubmit, placeholder, className }: SymbolAutocompleteProps) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const query = value.toUpperCase().trim();
  const suggestions = query.length > 0
    ? ALL_SYMBOLS.filter((s) => s.toUpperCase().includes(query)).slice(0, 8)
    : [];

  useEffect(() => {
    setSelectedIndex(-1);
  }, [value]);

  function handleSelect(symbol: string) {
    onChange(symbol);
    setShowSuggestions(false);
    inputRef.current?.focus();
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (!showSuggestions || suggestions.length === 0) {
      if (e.key === 'Enter') onSubmit?.();
      return;
    }

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => Math.min(prev + 1, suggestions.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (selectedIndex >= 0 && selectedIndex < suggestions.length) {
        handleSelect(suggestions[selectedIndex]);
      } else {
        onSubmit?.();
      }
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
    }
  }

  return (
    <div className="relative flex-1">
      <input
        ref={inputRef}
        type="text"
        value={value}
        onChange={(e) => {
          onChange(e.target.value.toUpperCase());
          setShowSuggestions(true);
        }}
        onFocus={() => setShowSuggestions(true)}
        onBlur={() => setTimeout(() => setShowSuggestions(false), 150)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder ?? 'e.g. HDFCBANK.NS, BTCUSDT'}
        className={className ?? 'w-full bg-bg-secondary border border-border-default rounded-lg px-3 py-2 text-sm font-mono text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-purple'}
        role="combobox"
        aria-expanded={showSuggestions && suggestions.length > 0}
        aria-autocomplete="list"
      />
      {showSuggestions && suggestions.length > 0 && (
        <ul
          ref={listRef}
          role="listbox"
          className="absolute z-50 top-full mt-1 w-full bg-bg-secondary border border-border-default rounded-lg shadow-lg overflow-hidden"
        >
          {suggestions.map((s, i) => {
            const marketType = s.endsWith('.NS') ? '📈' : s.endsWith('USDT') ? '🪙' : '💱';
            return (
              <li
                key={s}
                role="option"
                aria-selected={i === selectedIndex}
                onMouseDown={() => handleSelect(s)}
                className={`px-3 py-2 text-sm font-mono cursor-pointer flex items-center gap-2 ${
                  i === selectedIndex
                    ? 'bg-accent-purple/20 text-accent-purple'
                    : 'text-text-primary hover:bg-bg-card'
                }`}
              >
                <span>{marketType}</span>
                <span>{s}</span>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
