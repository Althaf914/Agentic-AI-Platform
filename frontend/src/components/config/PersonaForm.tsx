import { useState } from "react";
import type { PersonaConfig } from "@/types/config";

interface PersonaFormProps {
  defaultValues?: Partial<PersonaConfig>;
  onSave: (data: PersonaConfig) => void;
}

export default function PersonaForm({ defaultValues, onSave }: PersonaFormProps) {
  const [name, setName] = useState(defaultValues?.name ?? "");
  const [roleKeywords, setRoleKeywords] = useState(defaultValues?.role_keywords?.join(", ") ?? "");
  const [departments, setDepartments] = useState(defaultValues?.departments?.join(", ") ?? "");
  const [linkedinKeywords, setLinkedinKeywords] = useState(defaultValues?.linkedin_keywords?.join(", ") ?? "");
  const [priority, setPriority] = useState(defaultValues?.priority ?? 3);

  const handleSave = () => {
    onSave({
      name,
      role_keywords: roleKeywords.split(",").map((s) => s.trim()).filter(Boolean),
      departments: departments.split(",").map((s) => s.trim()).filter(Boolean),
      linkedin_keywords: linkedinKeywords.split(",").map((s) => s.trim()).filter(Boolean),
      priority,
    });
  };

  return (
    <div className="space-y-4">
      <div><label className="block text-xs font-medium text-foreground mb-1">Persona Name</label><input value={name} onChange={(e) => setName(e.target.value)} placeholder="VP of Engineering" className="w-full px-3 py-1.5 text-sm border border-input rounded-md bg-background" /></div>
      <div><label className="block text-xs font-medium text-foreground mb-1">Role Keywords</label><input value={roleKeywords} onChange={(e) => setRoleKeywords(e.target.value)} placeholder="VP, Director, Head" className="w-full px-3 py-1.5 text-sm border border-input rounded-md bg-background" /></div>
      <div><label className="block text-xs font-medium text-foreground mb-1">Departments</label><input value={departments} onChange={(e) => setDepartments(e.target.value)} placeholder="Engineering, Sales, Product" className="w-full px-3 py-1.5 text-sm border border-input rounded-md bg-background" /></div>
      <div><label className="block text-xs font-medium text-foreground mb-1">LinkedIn Keywords</label><input value={linkedinKeywords} onChange={(e) => setLinkedinKeywords(e.target.value)} placeholder="scaling, hiring, growth" className="w-full px-3 py-1.5 text-sm border border-input rounded-md bg-background" /></div>
      <div>
        <div className="flex justify-between text-xs"><span className="text-foreground font-medium">Priority</span><span className="text-muted-foreground">{priority}/5</span></div>
        <input type="range" min={1} max={5} step={1} value={priority} onChange={(e) => setPriority(+e.target.value)} className="w-full mt-1" />
      </div>
      <button onClick={handleSave} disabled={!name} className="w-full py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 disabled:opacity-50">Save Persona</button>
    </div>
  );
}
