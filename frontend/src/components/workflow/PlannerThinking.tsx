import { useState, useEffect } from "react";
import { motion } from "framer-motion";

interface PlannerThinkingProps {
  text: string;
  isStreaming: boolean;
}

export default function PlannerThinking({ text, isStreaming }: PlannerThinkingProps) {
  const [displayed, setDisplayed] = useState("");

  useEffect(() => {
    if (!isStreaming) {
      setDisplayed(text);
      return;
    }
    setDisplayed("");
    let idx = 0;
    const interval = setInterval(() => {
      if (idx < text.length) {
        setDisplayed(text.slice(0, idx + 1));
        idx++;
      } else {
        clearInterval(interval);
      }
    }, 20);
    return () => clearInterval(interval);
  }, [text, isStreaming]);

  if (!text) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="rounded-xl border overflow-hidden"
      style={{ backgroundColor: "#0d0d1a", borderColor: "var(--border)" }}
    >
      <div className="px-4 py-3 border-b flex items-center gap-2" style={{ borderColor: "var(--border)" }}>
        <span className="text-sm">🧠</span>
        <span className="text-xs font-semibold text-[#a855f7]">Planner Reasoning</span>
        {isStreaming && (
          <motion.span
            animate={{ opacity: [1, 0.3, 1] }}
            transition={{ duration: 0.8, repeat: Infinity }}
            className="w-2 h-2 rounded-full bg-[#a855f7] ml-auto"
          />
        )}
      </div>
      <pre className="p-4 text-xs text-[#8888aa] font-mono whitespace-pre-wrap leading-relaxed max-h-40 overflow-y-auto">
        {displayed}
        {isStreaming && <span className="text-[#a855f7]">▋</span>}
      </pre>
    </motion.div>
  );
}
