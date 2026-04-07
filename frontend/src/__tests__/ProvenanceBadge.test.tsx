/**
 * Tests for ProvenanceBadge component.
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProvenanceBadge, inferProvenance } from '@/components/graph/ProvenanceBadge';

describe('inferProvenance', () => {
  it('returns seed for null/undefined source', () => {
    expect(inferProvenance(null)).toBe('seed');
    expect(inferProvenance(undefined)).toBe('seed');
    expect(inferProvenance('')).toBe('seed');
  });

  it('returns ai for claude/extraction sources', () => {
    expect(inferProvenance('claude-extraction-abc123')).toBe('ai');
    expect(inferProvenance('Claude v3.5')).toBe('ai');
    expect(inferProvenance('llm-pipeline')).toBe('ai');
    expect(inferProvenance('ai-generated')).toBe('ai');
  });

  it('returns news for article/news sources', () => {
    expect(inferProvenance('reuters-article-12345')).toBe('news');
    expect(inferProvenance('bloomberg-article-2024')).toBe('news');
    expect(inferProvenance('rss_feed_economic_times')).toBe('news');
    expect(inferProvenance('article-001')).toBe('news');
    expect(inferProvenance('news-source-123')).toBe('news');
  });

  it('returns unknown for unrecognized sources', () => {
    expect(inferProvenance('manual-entry')).toBe('unknown');
    expect(inferProvenance('foobar')).toBe('unknown');
  });
});

describe('ProvenanceBadge', () => {
  it('renders curated badge for seed data', () => {
    render(<ProvenanceBadge source={null} showLabel />);
    expect(screen.getByText('Curated')).toBeInTheDocument();
    expect(screen.getByText('🌱')).toBeInTheDocument();
  });

  it('renders AI badge for AI-extracted data', () => {
    render(<ProvenanceBadge source="claude-extraction-123" showLabel />);
    expect(screen.getByText('AI-Extracted')).toBeInTheDocument();
    expect(screen.getByText('🤖')).toBeInTheDocument();
  });

  it('renders news badge for news-sourced data', () => {
    render(<ProvenanceBadge source="reuters-article-456" showLabel />);
    expect(screen.getByText('News-Sourced')).toBeInTheDocument();
    expect(screen.getByText('📰')).toBeInTheDocument();
  });

  it('renders unknown badge for unrecognized source', () => {
    render(<ProvenanceBadge source="manual-entry" showLabel />);
    expect(screen.getByText('Unknown')).toBeInTheDocument();
  });

  it('hides label by default', () => {
    render(<ProvenanceBadge source={null} />);
    expect(screen.getByText('🌱')).toBeInTheDocument();
    expect(screen.queryByText('Curated')).not.toBeInTheDocument();
  });

  it('shows title with source info', () => {
    render(<ProvenanceBadge source="reuters-article-456" />);
    const badge = screen.getByTitle('News-Sourced — source: reuters-article-456');
    expect(badge).toBeInTheDocument();
  });

  it('shows seed data title when source is null', () => {
    render(<ProvenanceBadge source={null} />);
    const badge = screen.getByTitle('Curated — source: seed data');
    expect(badge).toBeInTheDocument();
  });
});
