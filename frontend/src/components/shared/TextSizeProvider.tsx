'use client';

import { useEffect } from 'react';
import { usePreferencesStore } from '@/store/preferencesStore';

const SIZE_CLASSES: Record<string, string> = {
  small: 'text-size-small',
  medium: 'text-size-medium',
  large: 'text-size-large',
};

/**
 * Applies a CSS class to <html> based on the user's text size preference.
 * CSS custom properties in globals.css handle the actual scaling.
 */
export function TextSizeProvider() {
  const textSize = usePreferencesStore((s) => s.textSize);

  useEffect(() => {
    const html = document.documentElement;
    Object.values(SIZE_CLASSES).forEach((cls) => html.classList.remove(cls));
    html.classList.add(SIZE_CLASSES[textSize] || SIZE_CLASSES.medium);
  }, [textSize]);

  return null;
}
