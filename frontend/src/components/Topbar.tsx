import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { api, type HospitalSummary } from "../services/api";
import { AUTH_KEY } from "../pages/Login";

const PAGE_META: Record<string, { title: string; sub: string; crumb: string }> = {
  "/": { title: "Value-Based Care Command Center", sub: "Portfolio overview — Performance Year 2024", crumb: "VBC Portfolio / Command Center" },
  "/contracts": { title: "Contract Performance", sub: "Benchmark, settlement & quality across every contract", crumb: "VBC Portfolio / Contract Performance" },
  "/providers": { title: "Provider Variation", sub: "National provider cost & anomaly context", crumb: "VBC Portfolio / Provider Variation" },
  "/hospitals": { title: "Hospital Safety Quality", sub: "National hospital safety context", crumb: "VBC Portfolio / Hospital Quality" },
  "/opportunities": { title: "Review Opportunities", sub: "Ranked by driver score, ML confidence & financial relevance", crumb: "VBC Portfolio / Opportunities" },
  "/methodology": { title: "Methodology & Limitations", sub: "What the ML does — and doesn't — claim", crumb: "VBC Portfolio / Methodology" },
};

function metaFor(pathname: string) {
  if (PAGE_META[pathname]) return PAGE_META[pathname];
  if (pathname.startsWith("/hospitals/")) return { title: "Facility Profile", sub: "National context — not attributed to any ACO", crumb: "VBC Portfolio / Hospital Quality / Facility" };
  if (pathname.startsWith("/acos/")) return { title: "ACO Detail", sub: "Contract Health, drivers & ML profile", crumb: "VBC Portfolio / Command Center / ACO" };
  return { title: "VBC Command Center", sub: "", crumb: "VBC Portfolio" };
}

export default function Topbar() {
  const location = useLocation();
  const navigate = useNavigate();
  const meta = metaFor(location.pathname);
  const [hospitals, setHospitals] = useState<HospitalSummary[]>([]);
  const [userEmail, setUserEmail] = useState<string | null>(null);

  useEffect(() => {
    api.hospitals(500).then((d) => setHospitals(d.hospitals)).catch(() => {});
    try {
      const raw = localStorage.getItem(AUTH_KEY);
      if (raw) setUserEmail(JSON.parse(raw).email ?? null);
    } catch {
      /* ignore malformed auth blob */
    }
  }, []);

  function handleHospitalPick(e: React.ChangeEvent<HTMLSelectElement>) {
    const id = e.target.value;
    if (id) navigate(`/hospitals/${id}`);
    e.target.value = "";
  }

  function signOut() {
    localStorage.removeItem(AUTH_KEY);
    navigate("/login", { replace: true });
  }

  const initials = (userEmail || "A A").split(/[@.]/)[0].slice(0, 2).toUpperCase();

  return (
    <header
      className="sticky top-0 z-20 flex items-center justify-between gap-4 px-7 py-3.5 flex-wrap"
      style={{ background: "var(--paper-raised)", borderBottom: "1px solid var(--border)" }}
    >
      <div className="min-w-0">
        <div className="text-[11px] font-semibold" style={{ color: "var(--slate-light)" }}>{meta.crumb}</div>
        <div className="text-[16.5px] font-extrabold truncate" style={{ color: "var(--ink)" }}>{meta.title}</div>
        {meta.sub && <div className="text-[11.5px] mt-0.5" style={{ color: "var(--slate-light)" }}>{meta.sub}</div>}
      </div>

      <div className="flex items-center gap-2.5 flex-wrap">
        <span
          className="text-[10.5px] font-bold uppercase px-2.5 py-1.5 rounded-lg"
          style={{ background: "var(--accent-bg)", color: "var(--accent)" }}
          title="Every number in this app is read from precomputed pipeline output — nothing is recomputed or streamed live."
        >
          Batch ML · Precomputed
        </span>

        <select
          defaultValue=""
          onChange={handleHospitalPick}
          className="text-[12px] font-semibold rounded-lg px-2.5 py-1.5 outline-none"
          style={{ border: "1px solid var(--border)", background: "var(--surface-2)", color: "var(--slate)" }}
        >
          <option value="" disabled>Jump to hospital…</option>
          {hospitals.map((h) => (
            <option key={h["Facility ID"]} value={h["Facility ID"]}>{h["Facility Name"]} ({h.State})</option>
          ))}
        </select>

        <div className="flex items-center gap-2 pl-1">
          <div
            className="w-7 h-7 rounded-full flex items-center justify-center text-white text-[11px] font-bold shrink-0"
            style={{ background: "linear-gradient(135deg,#2461EA,#0D9488)" }}
          >
            {initials}
          </div>
          <button onClick={signOut} className="text-[11.5px] font-semibold" style={{ color: "var(--slate-light)" }}>
            Sign out
          </button>
        </div>
      </div>
    </header>
  );
}
