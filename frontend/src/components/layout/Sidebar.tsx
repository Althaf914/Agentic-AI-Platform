import { NavLink } from "react-router-dom";
import { useAuthStore } from "@/store/authStore";
import { useAuth } from "@/hooks/useAuth";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: "📊", color: "text-[#4f7cff]" },
  { to: "/icp", label: "ICP Builder", icon: "🎯", color: "text-[#22d3a5]", roles: ["admin", "sales"] },
  { to: "/personas", label: "Personas", icon: "👥", color: "text-[#a855f7]", roles: ["admin", "sales"] },
  { to: "/workflow", label: "Launch Workflow", icon: "🚀", color: "text-[#f59e0b]" },
  { to: "/workflows", label: "History", icon: "🕐", color: "text-[#8888aa]" },
  { to: "/prospects", label: "Prospects", icon: "🏢", color: "text-[#4f7cff]" },
  { to: "/approvals", label: "Approvals", icon: "✅", color: "text-[#22d3a5]", roles: ["admin", "sales"] },
  { to: "/memory", label: "Memory", icon: "🧠", color: "text-[#ec4899]" },
  { to: "/settings", label: "Settings", icon: "⚙️", color: "text-[#8888aa]", roles: ["admin"] },
];

export default function Sidebar() {
  const { user } = useAuthStore();
  const { logout } = useAuth();

  const filteredItems = NAV_ITEMS.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role))
  );

  return (
    <aside className="w-64 h-screen sticky top-0 flex flex-col border-r border-[--border]" style={{ backgroundColor: "var(--bg-secondary)" }}>
      {/* Logo */}
      <div className="px-5 py-5 border-b border-[--border]">
        <div className="flex items-center gap-2">
          <span className="text-xl">⚡</span>
          <h1 className="text-lg font-bold text-[--text-primary] tracking-tight">
            AgentForge
            <span className="ml-1.5 text-[10px] px-1.5 py-0.5 rounded bg-[#00abe4]/15 text-[#00abe4] font-semibold">AI</span>
          </h1>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {filteredItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive
                  ? "bg-[#00abe4]/10 text-[#00abe4] border-l-[3px] border-[#00abe4] ml-0 font-semibold shadow-sm"
                  : "text-[--text-secondary] hover:bg-[--bg-card-hover] hover:text-[--accent-blue] border-l-[3px] border-transparent"
              }`
            }
          >
            <span className="text-base">{item.icon}</span>
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User */}
      {user && (
        <div className="px-4 py-4 border-t border-[--border]">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-[#00abe4]/10 flex items-center justify-center text-xs font-bold text-[#00abe4] border border-[#00abe4]/20">
              {user.email[0].toUpperCase()}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-[--text-primary] font-medium truncate">{user.email}</p>
              <p className="text-[10px] text-[--text-muted]">{user.role}</p>
            </div>
            <button onClick={logout} className="text-[10px] text-[--text-muted] hover:text-[--accent-red] transition-colors">
              ✕
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}
