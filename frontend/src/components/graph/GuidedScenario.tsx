/**
 * GuidedScenario — step-by-step walkthroughs teaching users
 * how to use the knowledge graph effectively.
 *
 * Pre-built scenarios guide users through entity exploration,
 * impact simulation, and supply chain analysis.
 */
'use client';

import { useState } from 'react';
import Link from 'next/link';

interface WalkthroughStep {
  title: string;
  description: string;
  action: string;
  link?: string;
}

interface Walkthrough {
  id: string;
  emoji: string;
  title: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  duration: string;
  steps: WalkthroughStep[];
}

const WALKTHROUGHS: Walkthrough[] = [
  {
    id: 'explore-entity',
    emoji: '🔍',
    title: 'Explore an Entity',
    description: 'Learn to navigate entity details and discover supply chain connections.',
    difficulty: 'beginner',
    duration: '2 min',
    steps: [
      {
        title: 'Search for an entity',
        description: 'Use the search bar on the main Supply Chain Map page to find a company like "TCS" or "TSMC".',
        action: 'Go to Supply Chain Map and search',
        link: '/knowledge-graph',
      },
      {
        title: 'View entity details',
        description: 'Click on the entity card to see its full profile — type, tags, and creation date.',
        action: 'Click an entity from search results',
      },
      {
        title: 'Explore connections',
        description: 'On the entity detail page, see the connection graph. Use the hop selector (1/2/3) to see deeper connections.',
        action: 'Try different hop depths',
      },
      {
        title: 'Browse relationships',
        description: 'Scroll down to the Relationships table. Sort by weight or confidence. Check the Freshness and Provenance columns.',
        action: 'Sort by confidence to see strongest links',
      },
    ],
  },
  {
    id: 'run-simulation',
    emoji: '⚡',
    title: 'Run an Impact Simulation',
    description: 'Trace how a disruption event ripples through the supply chain.',
    difficulty: 'beginner',
    duration: '3 min',
    steps: [
      {
        title: 'Open the Impact Simulator',
        description: 'Navigate to the Impact Simulator page from the main Supply Chain Map.',
        action: 'Go to Impact Simulator',
        link: '/knowledge-graph/simulate',
      },
      {
        title: 'Try a Quick Scenario',
        description: 'Click one of the pre-built scenario cards (e.g., "Taiwan Earthquake"). The system automatically finds the trigger entity and runs the simulation.',
        action: 'Click a scenario card',
      },
      {
        title: 'Read impact results',
        description: 'Review the Impact Table showing which entities are affected and by how much. Switch to Chain Analysis to see narrative explanations.',
        action: 'Toggle between Impact Table and Chain Analysis',
      },
      {
        title: 'Run a custom simulation',
        description: 'Use the custom simulator below to search for any entity, set impact parameters, and run your own "what if?" scenario.',
        action: 'Search for an entity and click Run Simulation',
      },
    ],
  },
  {
    id: 'analyze-supply-chain',
    emoji: '🔗',
    title: 'Analyze Supply Chain Risk',
    description: 'Evaluate concentration risk and single-source dependencies.',
    difficulty: 'intermediate',
    duration: '5 min',
    steps: [
      {
        title: 'Review graph statistics',
        description: 'Check Graph Analytics to see entity type distribution, relationship breakdowns, and the most connected nodes.',
        action: 'Go to Graph Analytics',
        link: '/knowledge-graph/stats',
      },
      {
        title: 'Identify key hubs',
        description: 'The "Most Connected" section shows entities with the most relationships — these are potential single points of failure.',
        action: 'Note entities with >5 connections',
      },
      {
        title: 'Explore a hub entity',
        description: 'Click on a highly-connected entity to see its full relationship graph. Look for entities that many others depend on.',
        action: 'Open the drawer for a hub entity',
      },
      {
        title: 'Simulate hub failure',
        description: 'Go to Impact Simulator and simulate a disruption to the hub entity. See how many entities are affected at depth ≥2.',
        action: 'Run a simulation on a hub entity',
        link: '/knowledge-graph/simulate',
      },
      {
        title: 'Check alerts',
        description: 'Review Supply Chain Alerts for any AI-generated warnings about concentration risks.',
        action: 'Go to Alerts',
        link: '/knowledge-graph/alerts',
      },
    ],
  },
  {
    id: 'signal-context',
    emoji: '📊',
    title: 'Understand Signal Context',
    description: 'See how supply chain data enriches trading signals.',
    difficulty: 'intermediate',
    duration: '3 min',
    steps: [
      {
        title: 'Open a trading signal',
        description: 'From the main dashboard, click on any active signal for a company (stocks work best).',
        action: 'Go to Dashboard',
        link: '/',
      },
      {
        title: 'Find Supply Chain Context',
        description: 'On the signal detail page, scroll to the "Supply Chain Context" section and expand it.',
        action: 'Expand the Supply Chain Context section',
      },
      {
        title: 'Explore connections',
        description: 'See the entity\'s supply chain neighbors. Click any entity to open the drawer with quick details.',
        action: 'Click a connected entity',
      },
      {
        title: 'Run impact simulation',
        description: 'Click "Run Impact Sim" to see how disruptions to this company would ripple through the supply chain.',
        action: 'Launch simulation from signal context',
      },
    ],
  },
];

const DIFFICULTY_COLORS: Record<string, string> = {
  beginner: '#22C55E',
  intermediate: '#F59E0B',
  advanced: '#EF4444',
};

export function GuidedScenario() {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);

  const active = WALKTHROUGHS.find((w) => w.id === activeId);

  return (
    <div className="space-y-4">
      {!active ? (
        /* Walkthrough cards */
        <div className="grid sm:grid-cols-2 gap-3">
          {WALKTHROUGHS.map((w) => {
            const dColor = DIFFICULTY_COLORS[w.difficulty] || '#6B7280';
            return (
              <button
                key={w.id}
                onClick={() => {
                  setActiveId(w.id);
                  setCurrentStep(0);
                }}
                className="text-left p-4 rounded-xl border border-border-default bg-bg-secondary
                           hover:border-accent-purple/30 hover:bg-accent-purple/5 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{w.emoji}</span>
                  <div>
                    <h3 className="text-sm font-display font-semibold text-text-primary mb-0.5">
                      {w.title}
                    </h3>
                    <p className="text-xs text-text-muted mb-2">{w.description}</p>
                    <div className="flex items-center gap-2 text-[10px]">
                      <span
                        className="px-1.5 py-0.5 rounded-full font-mono capitalize"
                        style={{ backgroundColor: `${dColor}15`, color: dColor }}
                      >
                        {w.difficulty}
                      </span>
                      <span className="text-text-muted">⏱ {w.duration}</span>
                      <span className="text-text-muted">{w.steps.length} steps</span>
                    </div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      ) : (
        /* Active walkthrough */
        <div className="rounded-xl border border-accent-purple/20 bg-accent-purple/5 p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-display font-semibold text-text-primary">
                {active.emoji} {active.title}
              </h3>
              <p className="text-xs text-text-muted mt-0.5">
                Step {currentStep + 1} of {active.steps.length}
              </p>
            </div>
            <button
              onClick={() => setActiveId(null)}
              className="text-xs text-text-muted hover:text-text-secondary"
            >
              ✕ Close
            </button>
          </div>

          {/* Progress bar */}
          <div className="flex gap-1 mb-4">
            {active.steps.map((_, i) => (
              <div
                key={i}
                className="h-1 flex-1 rounded-full transition-colors"
                style={{
                  backgroundColor: i <= currentStep ? 'rgb(99,102,241)' : 'rgba(255,255,255,0.1)',
                }}
              />
            ))}
          </div>

          {/* Current step */}
          {(() => {
            const step = active.steps[currentStep];
            return (
              <div className="space-y-3">
                <h4 className="text-sm font-semibold text-text-primary">
                  {step.title}
                </h4>
                <p className="text-sm text-text-secondary">{step.description}</p>

                <div className="flex flex-wrap items-center gap-2 pt-2">
                  {step.link && (
                    <Link
                      href={step.link}
                      className="px-3 py-1.5 text-xs rounded-lg bg-accent-purple text-white
                                 hover:bg-accent-purple/90 font-medium transition-colors"
                    >
                      {step.action} →
                    </Link>
                  )}
                  {!step.link && (
                    <span className="px-3 py-1.5 text-xs rounded-lg border border-border-default text-text-secondary">
                      {step.action}
                    </span>
                  )}

                  <div className="flex gap-2 ml-auto">
                    <button
                      onClick={() => setCurrentStep((s) => Math.max(0, s - 1))}
                      disabled={currentStep === 0}
                      className="px-3 py-1.5 text-xs rounded-lg border border-border-default text-text-muted
                                 hover:border-border-hover disabled:opacity-30 disabled:cursor-not-allowed"
                    >
                      ← Back
                    </button>
                    {currentStep < active.steps.length - 1 ? (
                      <button
                        onClick={() => setCurrentStep((s) => s + 1)}
                        className="px-3 py-1.5 text-xs rounded-lg bg-accent-purple/10 text-accent-purple
                                   hover:bg-accent-purple/20 font-medium"
                      >
                        Next →
                      </button>
                    ) : (
                      <button
                        onClick={() => setActiveId(null)}
                        className="px-3 py-1.5 text-xs rounded-lg bg-signal-buy/10 text-signal-buy
                                   hover:bg-signal-buy/20 font-medium"
                      >
                        ✓ Complete
                      </button>
                    )}
                  </div>
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}
