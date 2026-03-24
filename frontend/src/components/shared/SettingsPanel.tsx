'use client';

import { usePreferencesStore, type ViewMode, type TextSize } from '@/store/preferencesStore';

const VIEW_OPTIONS: { value: ViewMode; label: string; desc: string }[] = [
  { value: 'simple', label: 'Simple', desc: 'Symbol, action, AI reason only' },
  { value: 'standard', label: 'Standard', desc: 'Full signal details' },
];

const TEXT_SIZES: { value: TextSize; label: string }[] = [
  { value: 'small', label: 'A' },
  { value: 'medium', label: 'A' },
  { value: 'large', label: 'A' },
];

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const { viewMode, setViewMode, textSize, setTextSize } = usePreferencesStore();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4" onClick={onClose}>
      <div
        className="bg-bg-secondary border border-border-default rounded-2xl max-w-sm w-full p-6 shadow-2xl space-y-5"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-display font-bold">Settings</h2>
          <button onClick={onClose} className="text-text-muted hover:text-text-primary text-sm">✕</button>
        </div>

        {/* View Mode */}
        <div>
          <label className="text-xs text-text-muted uppercase tracking-wider block mb-2">View Mode</label>
          <div className="flex gap-2">
            {VIEW_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setViewMode(opt.value)}
                className={`flex-1 px-3 py-2 rounded-lg border text-sm transition-colors ${
                  viewMode === opt.value
                    ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                    : 'border-border-default text-text-secondary hover:border-border-hover'
                }`}
              >
                <span className="font-medium block">{opt.label}</span>
                <span className="text-[10px] text-text-muted block mt-0.5">{opt.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Text Size */}
        <div>
          <label className="text-xs text-text-muted uppercase tracking-wider block mb-2">Text Size</label>
          <div className="flex gap-2">
            {TEXT_SIZES.map((opt, i) => {
              const fontSize = i === 0 ? 'text-xs' : i === 1 ? 'text-sm' : 'text-base';
              return (
                <button
                  key={opt.value}
                  onClick={() => setTextSize(opt.value)}
                  className={`flex-1 py-2 rounded-lg border transition-colors ${fontSize} font-display font-bold ${
                    textSize === opt.value
                      ? 'border-accent-purple text-accent-purple bg-accent-purple/10'
                      : 'border-border-default text-text-secondary hover:border-border-hover'
                  }`}
                >
                  {opt.label}
                  <span className="block text-[10px] font-normal text-text-muted mt-0.5">
                    {opt.value.charAt(0).toUpperCase() + opt.value.slice(1)}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        <button
          onClick={onClose}
          className="w-full py-2 bg-accent-purple text-white rounded-lg text-sm font-medium hover:bg-accent-purple/90 transition-colors"
        >
          Done
        </button>
      </div>
    </div>
  );
}
