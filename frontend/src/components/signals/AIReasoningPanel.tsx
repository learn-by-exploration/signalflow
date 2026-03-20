interface AIReasoningPanelProps {
  reasoning: string;
  isExpanded: boolean;
}

export function AIReasoningPanel({ reasoning, isExpanded }: AIReasoningPanelProps) {
  if (!isExpanded) return null;

  return (
    <div className="mt-3 pt-3 border-t border-border-default">
      <div className="flex items-start gap-2">
        <span className="text-base mt-0.5">🤖</span>
        <div>
          <p className="text-xs font-display font-medium text-accent-purple mb-1">AI Reasoning</p>
          <p className="text-sm text-text-secondary leading-relaxed">{reasoning}</p>
        </div>
      </div>
    </div>
  );
}
