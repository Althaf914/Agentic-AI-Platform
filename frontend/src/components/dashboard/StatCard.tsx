interface StatCardProps {
  label: string;
  value: string | number;
  icon: string;
  trend?: { direction: "up" | "down"; pct: number };
}

export default function StatCard({ label, value, icon, trend }: StatCardProps) {
  return (
    <div className="bg-card border border-border rounded-lg p-4 flex items-center gap-4">
      <span className="text-2xl">{icon}</span>
      <div className="flex-1 min-w-0">
        <p className="text-2xl font-bold text-foreground">{value}</p>
        <p className="text-xs text-muted-foreground truncate">{label}</p>
      </div>
      {trend && (
        <span className={`text-xs font-medium ${trend.direction === "up" ? "text-green-600" : "text-red-600"}`}>
          {trend.direction === "up" ? "↑" : "↓"} {trend.pct}%
        </span>
      )}
    </div>
  );
}
