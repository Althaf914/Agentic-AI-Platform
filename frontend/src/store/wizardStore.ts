import { create } from "zustand";

// ─── Types ────────────────────────────────────────────────────────────────────

export interface PrimaryPersona {
  title: string;
  seniority: string;
  department: string;
}

export interface WizardData {
  currentStep: number;
  campaignName: string;
  stepData: {
    step1_business: {
      description: string;
      product_category: string;
      value_proposition: string;
      domain_preset: string;
    };
    step2_geography: {
      countries: string[];
      states: string[];
      cities: string[];
      remote_ok: boolean;
    };
    step3_company_filters: {
      industries: string[];
      min_employees: number;
      max_employees: number;
      funding_stages: string[];
      min_revenue: string;
      max_revenue: string;
      company_age_year: number;
      exclude_keywords: string[];
    };
    step4_technology: {
      required_tech: string[];
      nice_to_have_tech: string[];
      exclude_tech: string[];
      cloud_providers: string[];
    };
    step5_committee: {
      primary_persona: PrimaryPersona;
      secondary_personas: PrimaryPersona[];
      influencers: string[];
    };
    step6_scoring: {
      industry_match: number;
      location_match: number;
      hiring_signals: number;
      tech_stack_match: number;
      funding_stage: number;
      revenue_tier: number;
      employee_range: number;
      decision_makers_found: number;
    };
  };
}

export interface WizardState extends WizardData {
  // Actions
  nextStep: () => void;
  prevStep: () => void;
  goToStep: (step: number) => void;
  setStepData: <K extends keyof WizardData["stepData"]>(
    step: K,
    data: Partial<WizardData["stepData"][K]>
  ) => void;
  setCampaignName: (name: string) => void;
  applyPreset: (preset: Partial<WizardData["stepData"]>) => void;
  resetWizard: () => void;
}

// ─── Defaults ────────────────────────────────────────────────────────────────

const DEFAULTS: WizardData = {
  currentStep: 0,
  campaignName: "",
  stepData: {
    step1_business: {
      description: "",
      product_category: "",
      value_proposition: "",
      domain_preset: "",
    },
    step2_geography: {
      countries: [],
      states: [],
      cities: [],
      remote_ok: false,
    },
    step3_company_filters: {
      industries: [],
      min_employees: 1,
      max_employees: 10000,
      funding_stages: [],
      min_revenue: "",
      max_revenue: "",
      company_age_year: 0,
      exclude_keywords: [],
    },
    step4_technology: {
      required_tech: [],
      nice_to_have_tech: [],
      exclude_tech: [],
      cloud_providers: [],
    },
    step5_committee: {
      primary_persona: { title: "", seniority: "", department: "" },
      secondary_personas: [],
      influencers: [],
    },
    step6_scoring: {
      industry_match: 25,
      location_match: 10,
      hiring_signals: 15,
      tech_stack_match: 15,
      funding_stage: 15,
      revenue_tier: 5,
      employee_range: 10,
      decision_makers_found: 5,
    },
  },
};

// ─── Store ────────────────────────────────────────────────────────────────────

export const useWizardStore = create<WizardState>((set) => ({
  ...DEFAULTS,

  nextStep: () =>
    set((s) => ({ currentStep: Math.min(s.currentStep + 1, 5) })),

  prevStep: () =>
    set((s) => ({ currentStep: Math.max(s.currentStep - 1, 0) })),

  goToStep: (step) =>
    set({ currentStep: Math.max(0, Math.min(step, 5)) }),

  setStepData: (step, data) =>
    set((s) => ({
      stepData: {
        ...s.stepData,
        [step]: { ...s.stepData[step], ...data },
      },
    })),

  setCampaignName: (name) => set({ campaignName: name }),

  applyPreset: (preset) =>
    set((s) => ({
      stepData: { ...s.stepData, ...preset },
    })),

  resetWizard: () => set({ ...DEFAULTS }),
}));
