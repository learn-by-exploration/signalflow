export function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const dims = { sm: 'h-4 w-4', md: 'h-6 w-6', lg: 'h-10 w-10' }[size];
  return (
    <div
      className={`${dims} animate-spin rounded-full border-2 border-border-default border-t-accent-purple`}
      role="status"
      aria-label="Loading"
    />
  );
}
