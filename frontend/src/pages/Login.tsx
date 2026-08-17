import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";

export const AUTH_KEY = "vbc_auth";

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: string } };
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setError("Enter an email and password to continue.");
      return;
    }
    localStorage.setItem(AUTH_KEY, JSON.stringify({ email, signedInAt: Date.now() }));
    navigate(location.state?.from || "/", { replace: true });
  }

  return (
    <div
      className="min-h-screen flex items-center justify-center px-6"
      style={{ background: "linear-gradient(155deg, #0C1730 0%, #101B33 60%, #16234A 100%)" }}
    >
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-3 mb-8 justify-center">
          <div
            className="w-10 h-10 rounded-[10px] flex items-center justify-center text-white font-extrabold text-base"
            style={{ background: "linear-gradient(135deg, #1E5FE8, #0D9488)", boxShadow: "0 4px 14px rgba(36,97,234,0.35)" }}
          >
            VC
          </div>
          <div className="leading-tight">
            <div className="font-display text-[15px]" style={{ color: "#fff", fontWeight: 700 }}>Command Center</div>
            <div className="text-[11px] font-semibold uppercase" style={{ color: "#6E7CA0", letterSpacing: "0.5px" }}>VBC Portfolio</div>
          </div>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-xl p-7"
          style={{ background: "var(--paper-raised)", border: "1px solid var(--border)", boxShadow: "var(--glass-shadow)" }}
        >
          <h1 className="text-[17px] font-bold mb-1" style={{ color: "var(--ink)" }}>Sign in</h1>
          <p className="text-[12.5px] mb-5" style={{ color: "var(--slate-light)" }}>
            Payer contract-management access — Performance Year 2024.
          </p>

          {error && (
            <div className="rounded-lg px-3 py-2 mb-4 text-[12.5px] font-medium" style={{ background: "var(--loss-bg)", color: "var(--loss)" }}>
              {error}
            </div>
          )}

          <label className="block text-[11px] font-bold uppercase tracking-wide mb-1.5" style={{ color: "var(--slate-light)" }}>
            Work email
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="analyst@payer.com"
            className="w-full rounded-lg px-3 py-2.5 mb-4 text-[13.5px] outline-none"
            style={{ border: "1px solid var(--border)", background: "var(--surface-2)", color: "var(--ink)" }}
          />

          <label className="block text-[11px] font-bold uppercase tracking-wide mb-1.5" style={{ color: "var(--slate-light)" }}>
            Password
          </label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="w-full rounded-lg px-3 py-2.5 mb-5 text-[13.5px] outline-none"
            style={{ border: "1px solid var(--border)", background: "var(--surface-2)", color: "var(--ink)" }}
          />

          <button
            type="submit"
            className="w-full rounded-lg py-2.5 text-[13.5px] font-bold text-white"
            style={{ background: "var(--accent)" }}
          >
            Sign in
          </button>

          <p className="text-[11px] mt-4 text-center" style={{ color: "var(--slate-light)" }}>
            Demo access gate only — any email/password signs you in. No patient or claims data is exposed by this screen.
          </p>
        </form>
      </div>
    </div>
  );
}
