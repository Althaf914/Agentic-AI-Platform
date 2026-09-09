import { useAuthStore } from "@/store/authStore";
import { useLocation } from "react-router-dom";
import { useState, useEffect } from "react";

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/icp": "ICP Builder",
  "/personas": "Persona Builder",
  "/workflow": "Launch Workflow",
  "/workflows": "Workflow History",
  "/prospects": "Prospects",
  "/approvals": "Approvals",
  "/memory": "Shared Memory",
  "/settings": "Settings",
};

export default function TopBar() {
  const { user } = useAuthStore();
  const location = useLocation();
  const basePath = "/" + location.pathname.split("/")[1];
  const title = PAGE_TITLES[basePath] || "AgentForge AI";

  // Light/Dark mode state
  const [isLight, setIsLight] = useState(() => {
    return localStorage.getItem("theme") === "light";
  });

  useEffect(() => {
    const root = document.documentElement;
    if (isLight) {
      root.classList.add("light-theme");
      localStorage.setItem("theme", "light");
    } else {
      root.classList.remove("light-theme");
      localStorage.setItem("theme", "dark");
    }
  }, [isLight]);

  const toggleTheme = () => setIsLight(!isLight);

  return (
    <header
      className="h-14 border-b px-6 flex items-center justify-between sticky top-0 z-10"
      style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)" }}
    >
      <h2 className="text-base font-semibold text-[--text-primary]">{title}</h2>

      <div className="flex items-center gap-4">
        {/* Theme toggle button */}
        <button
          onClick={toggleTheme}
          className="text-sm p-1.5 rounded-lg border border-[--border] bg-[--bg-card] text-[--text-secondary] hover:text-[--accent-blue] hover:border-[--accent-blue]/40 transition-all shadow-sm flex items-center justify-center"
          title={isLight ? "Switch to Dark Mode" : "Switch to Light Mode"}
        >
          {isLight ? "🌙 Dark" : "☀️ Light"}
        </button>

        {/* Notification bell */}
        <button className="relative text-[--text-secondary] hover:text-[--accent-blue] transition-colors">
          <span className="text-lg">🔔</span>
          <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-[--accent-amber] text-[9px] font-bold text-white flex items-center justify-center">
            4
          </span>
        </button>

        {/* User */}
        {user && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-[#4f7cff]/20 flex items-center justify-center text-xs font-bold text-[#4f7cff]">
              {user.email[0].toUpperCase()}
            </div>
            <span className="text-xs px-2 py-0.5 rounded-full bg-[#4f7cff]/10 text-[#4f7cff] font-medium">
              {user.role}
            </span>
          </div>
        )}
      </div>
    </header>
  );
}
