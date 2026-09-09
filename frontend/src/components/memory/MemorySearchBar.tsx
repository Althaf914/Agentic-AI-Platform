import { useState, useEffect, useRef } from "react";
import { searchMemory } from "@/api/memory";
import type { MemoryEntry } from "@/types/memory";

interface MemorySearchBarProps {
  onResults: (entries: MemoryEntry[]) => void;
}

export default function MemorySearchBar({ onResults }: MemorySearchBarProps) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    if (!query.trim()) {
      onResults([]);
      return;
    }

    // Debounce 300ms
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setLoading(true);
      try {
        const results = await searchMemory(query, 10);
        onResults(results);
      } catch {
        onResults([]);
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [query, onResults]);

  return (
    <div className="relative">
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search memory (semantic)..."
        className="w-full px-4 py-2.5 border border-input rounded-lg bg-background text-foreground pr-10"
      />
      {loading && (
        <div className="absolute right-3 top-1/2 -translate-y-1/2">
          <div className="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
}
