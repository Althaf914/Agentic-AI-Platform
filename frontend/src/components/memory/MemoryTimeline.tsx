import type { MemoryEntry } from "@/types/memory";

interface MemoryTimelineProps {
  entries: MemoryEntry[];
  highlightQuery?: string;
}

const EVENT_ICONS: Record<string, string> = {
  company: "🏢",
  contact: "👤",
  workflow: "⚡",
};

function groupByDate(entries: MemoryEntry[]) {
  const today = new Date().toDateString();
  const yesterday = new Date(Date.now() - 86400000).toDateString();

  const groups: { label: string; items: MemoryEntry[] }[] = [
    { label: "Today", items: [] },
    { label: "Yesterday", items: [] },
    { label: "Older", items: [] },
  ];

  for (const entry of entries) {
    const d = new Date(entry.created_at).toDateString();
    if (d === today) groups[0].items.push(entry);
    else if (d === yesterday) groups[1].items.push(entry);
    else groups[2].items.push(entry);
  }

  return groups.filter((g) => g.items.length > 0);
}

function highlightText(text: string, query?: string) {
  if (!query || !query.trim()) return text;
  const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");
  const parts = text.split(regex);
  return parts.map((part, i) =>
    regex.test(part) ? <mark key={i} className="bg-yellow-200 dark:bg-yellow-800 rounded px-0.5">{part}</mark> : part
  );
}

export default function MemoryTimeline({ entries, highlightQuery }: MemoryTimelineProps) {
  const groups = groupByDate(entries);

  if (entries.length === 0) {
    return <p className="text-sm text-muted-foreground text-center py-8">No memory entries found</p>;
  }

  return (
    <div className="space-y-6">
      {groups.map((group) => (
        <div key={group.label}>
          <h4 className="text-xs font-semibold text-muted-foreground mb-2">{group.label}</h4>
          <div className="border-l-2 border-border pl-4 space-y-3">
            {group.items.map((entry) => (
              <div key={entry.id} className="relative">
                {/* Dot */}
                <div className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-primary border-2 border-background" />
                <div className="bg-card border border-border rounded-md p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span>{EVENT_ICONS[entry.entity_type] || "•"}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground">{entry.entity_type}</span>
                    <span className="text-[10px] text-muted-foreground ml-auto">{new Date(entry.created_at).toLocaleString()}</span>
                  </div>
                  <p className="text-xs text-foreground">{highlightText(entry.summary, highlightQuery)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
