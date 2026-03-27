'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useSession } from 'next-auth/react';
import { FocusTrap } from './FocusTrap';
import { NAV_MOBILE_MENU_GROUPS, NAV_LEGAL_LINKS } from '@/lib/constants';

interface MobileMenuSheetProps {
  isOpen: boolean;
  onClose: () => void;
}

export function MobileMenuSheet({ isOpen, onClose }: MobileMenuSheetProps) {
  const pathname = usePathname();
  const { status } = useSession();
  const isAuth = status === 'authenticated';

  // Prevent body scroll when sheet is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = '';
      };
    }
  }, [isOpen]);

  // Close on route change
  useEffect(() => {
    onClose();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pathname]);

  if (!isAuth || !isOpen) return null;

  return (
    <FocusTrap isOpen={isOpen} onClose={onClose}>
      {/* Overlay */}
      <div
        className="fixed inset-0 z-[60] bg-black/50 animate-overlay-in"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Sheet */}
      <div
        className="fixed bottom-0 left-0 right-0 z-[60] bg-bg-secondary rounded-t-2xl animate-sheet-up max-h-[70vh] overflow-y-auto"
        role="dialog"
        aria-modal="true"
        aria-label="Navigation menu"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Drag handle */}
        <div className="flex justify-center pt-3 pb-2">
          <div className="w-10 h-1 rounded-full bg-text-muted/30" />
        </div>

        {/* Groups */}
        <div className="px-4 pb-4">
          {NAV_MOBILE_MENU_GROUPS.map((group) => (
            <div key={group.title} className="mb-4">
              <p className="text-xs text-text-muted uppercase tracking-wider font-display font-semibold mb-2">
                {group.title}
              </p>
              {group.links.map((link) => {
                const isActive = pathname === link.href;
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={onClose}
                    className={`flex items-center gap-3 px-3 py-3 rounded-lg text-sm transition-colors ${
                      isActive
                        ? 'text-accent-purple bg-accent-purple/10 border-l-2 border-accent-purple'
                        : 'text-text-secondary hover:text-text-primary hover:bg-white/[0.03]'
                    }`}
                  >
                    <span className="text-base">{link.icon}</span>
                    {link.label}
                  </Link>
                );
              })}
            </div>
          ))}

          {/* Legal links */}
          <div className="border-t border-border-default pt-3 mt-2 flex flex-wrap gap-x-2 gap-y-1 justify-center">
            {NAV_LEGAL_LINKS.map((link, i) => (
              <span key={link.href} className="text-xs text-text-muted">
                {i > 0 && <span className="mr-2">·</span>}
                <Link
                  href={link.href}
                  onClick={onClose}
                  className="hover:text-text-secondary transition-colors"
                >
                  {link.label}
                </Link>
              </span>
            ))}
          </div>
        </div>
      </div>
    </FocusTrap>
  );
}
