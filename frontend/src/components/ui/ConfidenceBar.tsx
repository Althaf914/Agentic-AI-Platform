interface ConfidenceBarProps {
  confidence: number; // 0 to 1
  label?: string;
}

function barColor(pct: number) {
  if (pct > 70) return "bg-green-500";
  if (pct >= 40) return "bg-amber-500";
  return "bg-red-500";
}

export default function ConfidenceBar({ confidence, label }: ConfidenceBarProps) {
  const pct = Math.round(confidence * 100);

  return (
    <div className="space-y-1">
      {label && (
        <div className="flex justify-between text-[10px]">
          <span className="text-muted-foreground">{label}</span>
          <span className="text-foreground font-medium">{pct}%</span>
        </div>
      )}
      <div className="h-1.5 bg-muted rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all ${barColor(pct)}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
