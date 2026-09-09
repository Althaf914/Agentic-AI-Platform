import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { savePersona, listConfigs } from "@/api/configurations";
import type { ConfigItem } from "@/types/config";

export default function PersonaBuilder() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");
  const [roleKeywords, setRoleKeywords] = useState("");
  const [departments, setDepartments] = useState("");
  const [linkedinKeywords, setLinkedinKeywords] = useState("");
  const [priority, setPriority] = useState(1);

  const { data: configs = [] } = useQuery({ queryKey: ["configs"], queryFn: listConfigs });
  const personas = configs.filter((c: ConfigItem) => c.type === "persona");

  const mutation = useMutation({
    mutationFn: savePersona,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["configs"] });
      setName("");
      setRoleKeywords("");
      setDepartments("");
    },
  });

  const handleSave = () => {
    mutation.mutate({
      name,
      config_json: {
        name,
        role_keywords: roleKeywords.split(",").map((s) => s.trim()).filter(Boolean),
        departments: departments.split(",").map((s) => s.trim()).filter(Boolean),
        linkedin_keywords: linkedinKeywords.split(",").map((s) => s.trim()).filter(Boolean),
        priority,
      },
    });
  };

  return (
    <div className="space-y-6">
      <div className="bg-card border border-border rounded-lg p-6 space-y-4">
        <h3 className="font-semibold text-foreground">New Persona</h3>
        <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Persona name (e.g. VP Engineering)" className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" />
        <input value={roleKeywords} onChange={(e) => setRoleKeywords(e.target.value)} placeholder="Role keywords (VP, Director, Head)" className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" />
        <input value={departments} onChange={(e) => setDepartments(e.target.value)} placeholder="Departments (Engineering, Sales)" className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" />
        <input value={linkedinKeywords} onChange={(e) => setLinkedinKeywords(e.target.value)} placeholder="LinkedIn keywords" className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground" />
        <input type="number" value={priority} onChange={(e) => setPriority(+e.target.value)} min={1} max={5} className="w-24 px-3 py-2 border border-input rounded-md bg-background text-foreground" />
        <button onClick={handleSave} disabled={!name} className="px-4 py-2 bg-primary text-primary-foreground rounded-md font-medium hover:opacity-90 disabled:opacity-50">
          Save Persona
        </button>
      </div>

      <div className="space-y-2">
        <h3 className="font-semibold text-foreground">Saved Personas ({personas.length})</h3>
        {personas.map((p: ConfigItem) => (
          <div key={p.id} className="bg-card border border-border rounded-md p-3">
            <span className="text-sm font-medium text-foreground">{p.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
