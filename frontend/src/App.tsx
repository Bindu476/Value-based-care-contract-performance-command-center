import { BrowserRouter, Routes, Route, Link, Navigate, useLocation } from "react-router-dom";
import CommandCenter from "./pages/CommandCenter";
import AcoDetail from "./pages/AcoDetail";
import ContractPerformance from "./pages/ContractPerformance";
import ProviderVariation from "./pages/ProviderVariation";
import HospitalQuality from "./pages/HospitalQuality";
import HospitalDetail from "./pages/HospitalDetail";
import Opportunities from "./pages/Opportunities";
import ReviewBrief from "./pages/ReviewBrief";
import Methodology from "./pages/Methodology";
import Login, { AUTH_KEY } from "./pages/Login";
import Topbar from "./components/Topbar";
import { IconGrid, IconFileText, IconUsers, IconCross, IconBulb, IconBook } from "./components/icons";

const LINKS = [
  { to: "/", label: "Command Center", icon: IconGrid },
  { to: "/contracts", label: "Contract Performance", icon: IconFileText },
  { to: "/providers", label: "Provider Variation", icon: IconUsers },
  { to: "/hospitals", label: "Hospital Quality", icon: IconCross },
  { to: "/opportunities", label: "Opportunities", icon: IconBulb },
  { to: "/methodology", label: "Methodology", icon: IconBook },
];

function isAuthed() {
  return !!localStorage.getItem(AUTH_KEY);
}

function Sidebar() {
  const location = useLocation();
  return (
    <aside
      className="glass-panel print:hidden fixed left-0 top-0 h-screen flex flex-col shrink-0"
      style={{ width: "var(--sidebar-width)", borderRight: "1px solid var(--sidebar-border)" }}
    >
      <div className="px-5 pt-[22px] pb-[18px]" style={{ borderBottom: "1px solid var(--sidebar-border)" }}>
        <div className="flex items-center gap-[11px]">
          <div
            className="w-9 h-9 rounded-[9px] flex items-center justify-center shrink-0 text-white font-extrabold text-sm"
            style={{ background: "linear-gradient(135deg, #1E5FE8, #0D9488)", boxShadow: "0 4px 14px rgba(36,97,234,0.35)", letterSpacing: "-0.3px" }}
          >
            VC
          </div>
          <div className="leading-tight">
            <div className="font-display text-[14.5px]" style={{ color: "#fff", fontWeight: 700, letterSpacing: "0.1px" }}>Command Center</div>
            <div className="text-[11px] font-semibold uppercase mt-0.5" style={{ color: "var(--sidebar-ink-dim)", letterSpacing: "0.5px" }}>VBC Portfolio</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-3.5 space-y-0.5 overflow-y-auto">
        {LINKS.map((l) => {
          const active = location.pathname === l.to;
          const Icon = l.icon;
          return (
            <Link
              key={l.to}
              to={l.to}
              className="flex items-center gap-[11px] px-3 py-2.5 rounded-[9px] text-[13.5px] transition-colors"
              style={{
                background: active ? "rgba(36,97,234,0.16)" : "transparent",
                border: active ? "1px solid rgba(36,97,234,0.35)" : "1px solid transparent",
                color: active ? "#fff" : "var(--sidebar-ink)",
                fontWeight: 500,
              }}
            >
              <Icon className="shrink-0" style={{ color: active ? "#5B93F5" : undefined, opacity: active ? 1 : 0.85 }} />
              {l.label}
            </Link>
          );
        })}
      </nav>

      <div className="px-5 pb-[18px] pt-3.5" style={{ borderTop: "1px solid var(--sidebar-border)" }}>
        <div className="text-[10.5px] leading-relaxed" style={{ color: "var(--sidebar-ink-dim)" }}>
          <b style={{ color: "#8FA4CE" }}>Performance Year 2024</b>
          <br />
          CMS public data — see Methodology.
        </div>
      </div>
    </aside>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  const location = useLocation();

  if (!isAuthed()) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  const isReviewBrief = location.pathname.startsWith("/acos/") && location.pathname.includes("review-brief");
  if (isReviewBrief) return <>{children}</>;

  return (
    <>
      <Sidebar />
      <div style={{ marginLeft: "var(--sidebar-width)", minHeight: "100vh" }}>
        <Topbar />
        {children}
      </div>
    </>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="*"
          element={
            <Shell>
              <Routes>
                <Route path="/" element={<CommandCenter />} />
                <Route path="/contracts" element={<ContractPerformance />} />
                <Route path="/acos/:acoId" element={<AcoDetail />} />
                <Route path="/acos/:acoId/review-brief" element={<ReviewBrief />} />
                <Route path="/providers" element={<ProviderVariation />} />
                <Route path="/hospitals" element={<HospitalQuality />} />
                <Route path="/hospitals/:hospitalId" element={<HospitalDetail />} />
                <Route path="/opportunities" element={<Opportunities />} />
                <Route path="/methodology" element={<Methodology />} />
              </Routes>
            </Shell>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
