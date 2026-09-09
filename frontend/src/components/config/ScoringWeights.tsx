import { useState } from "react";
import type { ScoringConfig } from "@/types/config";

interface ScoringWeightsProps {
  defaultValues?: Partial<ScoringConfig>;
  onSave: (data: ScoringConfig) => void;
}

const LABELS: Record<string, string> = {
  funding_weight: "Funding",
  hiring_weight: "Hiring",
  revenue_weight: "Revenue",
  icp_match_weight: "ICP Match",
  tech_stack_weight: "Tech Stack",
  growth_weight: "Growth",
};

export default function ScoringWeights({ defaultValues, onSave }: ScoringWeightsProps) {
  const [weights, setWeights] = useState<ScoringConfig>({
    funding_weight: defaultValues?.funding_weight ?? 0.15,
    hiring_weight: defaultValues?.hiring_weight ?? 0.15,
    revenue_weight: defaultValues?.revenue_weight ?? 0.2,
    icp_match_weight: defaultValues?.icp_match_weight ?? 0.25,
    tech_stack_weight: defaultValues?.tech_stack_weight ?? 0.15,
    growth_weight: defaultValues?.growth_weight ?? 0.1,
  });

  const total = Object.values(weights).reduce((sum, v) => sum + v, 0);
  const isValid = Math.abs(total - 1) < 0.01;

  const update = (key: keyof ScoringConfig, val: number) => {
    setWeights({ ...weights, [key]: val });
  };

  return (
    <div className="space-y-4">
      {(Object.keys(LABELS) as (keyof ScoringConfig)[]).map((key) => (
        <div key={key}>
          <div className="flex justify-between text-xs">
            <span className="text-foreground font-medium">{LABELS[key]}</span>
            <span className="text-muted-foreground">{(weights[key] * 100).toFixed(0)}%</span>
          </div>
          <input
            type="range" min={0} max={100} step={5}
            value={weights[key] * 100}
            onChange={(e) => update(key, +e.target.value / 100)}
            className="w-full mt-1"
          />
        </div>
      ))}

      <div className={`text-xs font-medium ${isValid ? "text-green-600" : "text-red-600"}`}>
        Total: {(total * 100).toFixed(0)}% {!isValid && "(must equal 100%)"}
      </div>

      <button onClick={() => onSave(weights)} disabled={!isValid} className="w-full py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50">
        Save Scoring Config
      </button>
    </div>
  );
}
