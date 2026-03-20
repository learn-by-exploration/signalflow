'use client';

import { createContext, useCallback, useContext, useState } from 'react';

interface Toast {
  id: number;
  message: string;
  type: 'success' | 'error' | 'info';
}

interface ToastContextValue {
  toast: (message: string, type?: Toast['type']) => void;
}

const ToastContext = createContext<ToastContextValue>({ toast: () => {} });

export function useToast() {
  return useContext(ToastContext);
}

let nextId = 0;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const toast = useCallback((message: string, type: Toast['type'] = 'info') => {
    const id = ++nextId;
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3000);
  }, []);

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      {/* Toast container */}
      <div className="fixed bottom-16 right-4 z-[100] flex flex-col gap-2 pointer-events-none">
        {toasts.map((t) => {
          const bg =
            t.type === 'success'
              ? 'bg-signal-buy/15 border-signal-buy/30 text-signal-buy'
              : t.type === 'error'
                ? 'bg-signal-sell/15 border-signal-sell/30 text-signal-sell'
                : 'bg-accent-purple/15 border-accent-purple/30 text-accent-purple';
          return (
            <div
              key={t.id}
              className={`pointer-events-auto px-4 py-2.5 rounded-lg border text-sm font-display animate-slide-in ${bg}`}
            >
              {t.message}
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}
