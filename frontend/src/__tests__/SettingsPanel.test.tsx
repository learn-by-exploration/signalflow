import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { SettingsPanel } from '@/components/shared/SettingsPanel';

describe('SettingsPanel (deprecated)', () => {
  it('renders nothing (deprecated stub)', () => {
    const { container } = render(<SettingsPanel isOpen={true} onClose={() => {}} />);
    expect(container.innerHTML).toBe('');
  });

  it('renders nothing when closed', () => {
    const { container } = render(<SettingsPanel isOpen={false} onClose={() => {}} />);
    expect(container.innerHTML).toBe('');
  });
});
