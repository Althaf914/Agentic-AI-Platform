import { memo } from "react";
import { Handle, Position } from "reactflow";
import { motion, AnimatePresence } from "framer-motion";

interface AgentNodeData {
  label: string;
  status: "idle" | "running" | "completed" | "failed" | "skipped";
  agentName: string;
}

const NODE_STYLES: Record<string, string> = {
  idle: "border-[#2a2a3a] bg-[#16161f] text-[#8888aa]",
  running: "border-[#4f7cff] bg-[#0d1529] text-white shadow-[0_0_20px_rgba(79,124,255,0.4)]",
  completed: "border-[#22d3a5] bg-[#0d1f1a] text-white shadow-[0_0_15px_rgba(34,211,165,0.3)]",
  failed: "border-[#ef4444] bg-[#1f0d0d] text-white",
  skipped: "border-dashed border-[#55556a] bg-[#12121a] text-[#55556a]",
};

const STATUS_DOTS: Record<string, string> = {
  idle: "bg-[#55556a]",
  running: "bg-[#4f7cff] animate-pulse",
  completed: "bg-[#22d3a5]",
  failed: "bg-[#ef4444]",
  skipped: "bg-[#55556a]",
};

function AgentNode({ data }: { data: AgentNodeData }) {
  const { label, status } = data;

  return (
    <div className="relative">
      <Handle type="target" position={Position.Top} className="!bg-[#2a2a3a] !border-[#2a2a3a]" />

      <AnimatePresence mode="wait">
        <motion.div
          key={status}
          initial={{ opacity: 0.7, scale: 0.96 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.2 }}
          className={`relative w-[160px] h-[72px] rounded-xl border-2 flex flex-col items-center justify-center ${NODE_STYLES[status]}`}
        >
          {/* Pulse ring for running state */}
          {status === "running" && (
            <motion.div
              className="absolute inset-0 rounded-xl border-2 border-[#4f7cff]"
              animate={{ scale: [1, 1.06, 1], opacity: [0.6, 0.2, 0.6] }}
              transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
            />
          )}

          {/* Status dot top-right */}
          <span className={`absolute top-2 right-2 w-2.5 h-2.5 rounded-full ${STATUS_DOTS[status]}`} />

          <p className="text-xs font-semibold leading-tight text-center px-2">{label}</p>
          {status === "skipped" && (
            <p className="text-[9px] mt-0.5 italic">Skipped by Planner</p>
          )}
        </motion.div>
      </AnimatePresence>

      <Handle type="source" position={Position.Bottom} className="!bg-[#2a2a3a] !border-[#2a2a3a]" />
    </div>
  );
}

export default memo(AgentNode);
