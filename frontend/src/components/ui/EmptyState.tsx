interface EmptyStateProps {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
}

export default function EmptyState({ title, description, actionLabel, onAction }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
      {/* Simple SVG icon */}
      <svg className="w-16 h-16 text-muted-foreground/40 mb-4" fill="none" viewBox="0 0 64 64" stroke="currentColor" strokeWidth={1.5}>
        <rect x={12} y={16} width={40} height={36} rx={4} />
        <path d="M20 28h24M20 36h16M20 44h20" strokeLinecap="round" />
        <circle cx={32} cy={10} r={4} />
      </svg>
      <h3 className="text-lg font-semibold text-foreground">{title}</h3>
      <p className="text-sm text-muted-foreground mt-1 max-w-xs">{description}</p>
      {actionLabel && onAction && (
        <button onClick={onAction} className="mt-4 px-4 py-2 text-sm bg-primary text-primary-foreground rounded-md hover:opacity-90">
          {actionLabel}
        </button>
      )}
    </div>
  );
}
