import { useState } from "react";
import { useAuth } from "@/hooks/useAuth";

export default function Login() {
  const { login, isAuthenticated } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) {
    window.location.href = "/dashboard";
    return null;
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4" style={{ background: "var(--gradient-hero)" }}>
      <div className="w-full max-w-sm space-y-6">
        {/* Logo */}
        <div className="text-center">
          <div className="flex items-center justify-center gap-2 mb-2">
            <span className="text-3xl">⚡</span>
            <h1 className="text-2xl font-bold text-white">
              AgentForge
              <span className="ml-1.5 text-xs px-2 py-0.5 rounded bg-[#4f7cff]/20 text-[#4f7cff] font-semibold">AI</span>
            </h1>
          </div>
          <p className="text-[--text-secondary] text-sm">B2B Customer Discovery Platform</p>
        </div>

        {/* Form */}
        <form
          onSubmit={handleSubmit}
          className="space-y-4 p-6 rounded-xl border"
          style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}
        >
          {error && (
            <p className="text-xs text-[--accent-red] bg-[--accent-red]/10 px-3 py-2 rounded-lg">{error}</p>
          )}

          <div>
            <label className="block text-xs font-medium text-[--text-secondary] mb-1.5">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none transition-colors"
              style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }}
              placeholder="admin@agentforge.ai"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-[--text-secondary] mb-1.5">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg border text-sm focus:border-[#4f7cff] focus:outline-none transition-colors"
              style={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border)", color: "var(--text-primary)" }}
              placeholder="••••••••"
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-lg bg-[#4f7cff] text-white font-medium hover:shadow-[0_0_20px_rgba(79,124,255,0.4)] transition-all disabled:opacity-50"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <p className="text-[10px] text-center text-[--text-muted]">
          Demo: admin@agentforge.ai / demo1234
        </p>
      </div>
    </div>
  );
}
