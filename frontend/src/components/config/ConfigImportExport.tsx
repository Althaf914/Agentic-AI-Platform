import { useRef } from "react";
import { PRESET_CONFIGS } from "@/utils/constants";

interface ConfigImportExportProps {
  onImport: (data: Record<string, unknown>) => void;
  currentConfig?: Record<string, unknown>;
}

export default function ConfigImportExport({ onImport, currentConfig }: ConfigImportExportProps) {
  const fileRef = useRef<HTMLInputElement>(null);

  const handleExport = () => {
    if (!currentConfig) return;
    const blob = new Blob([JSON.stringify(currentConfig, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "agentforge-config.json"; a.click();
    URL.revokeObjectURL(url);
  };

  const handleImport = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const data = JSON.parse(reader.result as string);
        onImport(data);
      } catch {
        alert("Invalid JSON file");
      }
    };
    reader.readAsText(file);
  };

  const loadPreset = (key: "saas" | "staffing" | "cybersecurity") => {
    onImport(PRESET_CONFIGS[key]);
  };

  return (
    <div className="space-y-3 border border-border rounded-lg p-4">
      <h4 className="text-xs font-semibold text-foreground">Import / Export</h4>

      <div className="flex gap-2 flex-wrap">
        <button onClick={handleExport} disabled={!currentConfig} className="text-xs px-3 py-1.5 bg-muted rounded-md hover:bg-accent disabled:opacity-50">Export JSON</button>
        <button onClick={() => fileRef.current?.click()} className="text-xs px-3 py-1.5 bg-muted rounded-md hover:bg-accent">Import JSON</button>
        <input ref={fileRef} type="file" accept=".json" onChange={handleImport} className="hidden" />
      </div>

      <div>
        <p className="text-[10px] text-muted-foreground mb-1">Load Preset:</p>
        <div className="flex gap-2">
          <button onClick={() => loadPreset("saas")} className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200">B2B SaaS</button>
          <button onClick={() => loadPreset("staffing")} className="text-xs px-2 py-1 bg-teal-100 text-teal-700 rounded hover:bg-teal-200">Staffing</button>
          <button onClick={() => loadPreset("cybersecurity")} className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded hover:bg-purple-200">Cybersecurity</button>
        </div>
      </div>
    </div>
  );
}
