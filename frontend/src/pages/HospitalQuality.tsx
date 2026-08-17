import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import KPICard from "../components/KPICard";

interface Hospital {
  "Facility ID": number;
  "Facility Name": string;
  State: string;
  cluster_name: string;
  HAI_mean_score: number;
  anomaly_score: number;
  is_high_confidence_anomaly: boolean;
}

interface HospitalListResponse {
  hospitals: Hospital[];
  cluster_distribution: Record<string, number>;
  total_flagged: number;
  total_facilities: number;
}

export default function HospitalQuality() {
  const [data, setData] = useState<HospitalListResponse | null>(null);
  const [flaggedOnly, setFlaggedOnly] = useState(true);

  useEffect(() => {
    fetch(`/api/hospitals?flagged_only=${flaggedOnly}&limit=30`)
      .then((r) => r.json())
      .then(setData);
  }, [flaggedOnly]);

  if (!data) return <div className="p-8" style={{ color: "var(--slate)" }}>Loading hospital safety data...</div>;

  return (
    <div className="max-w-6xl mx-auto px-7 py-8">
      <Link to="/" className="text-[12.5px] font-semibold" style={{ color: "var(--slate-light)" }}>← Command Center</Link>
      <h1 className="font-display text-[19px] mt-3 mb-4" style={{ color: "var(--ink)" }}>Hospital Safety Quality</h1>

      <div
        className="rounded-xl border p-3.5 mb-5 text-xs font-medium"
        style={{ borderColor: "var(--border)", background: "var(--paper-raised)", color: "var(--slate)", boxShadow: "var(--glass-shadow)" }}
      >
        General portfolio context — hospitals shown here are <strong>not attributed to any specific ACO</strong>.
        No verified ACO-hospital crosswalk exists in this dataset (Section 3.4).
      </div>

      <section className="grid grid-cols-2 md:grid-cols-4 gap-3.5 mb-5">
        <KPICard label="Total Facilities" value={String(data.total_facilities)} />
        <KPICard label="Flagged (Anomalous)" value={String(data.total_flagged)} tone="anomaly" />
        <KPICard label="Stronger Safety" value={String(data.cluster_distribution["Stronger Safety Performance"] ?? 0)} tone="savings" />
        <KPICard label="Weaker Safety" value={String(data.cluster_distribution["Weaker Safety Performance"] ?? 0)} tone="loss" />
      </section>

      <div
        className="rounded-xl border p-3.5 mb-5 text-xs font-medium"
        style={{ borderColor: "#F1E0B6", background: "var(--anomaly-bg)", color: "var(--ink)" }}
      >
        <strong>Note on anomaly direction:</strong> flagged facilities are not all poor performers — of {data.total_flagged} flagged,
        roughly half show unusually strong safety scores and half show unusually weak ones. Anomaly means statistically
        unusual, not necessarily concerning.
      </div>

      <section
        className="rounded-xl border p-5"
        style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}
      >
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-[13.5px] font-bold" style={{ color: "var(--ink)" }}>Facilities</h2>
          <label className="flex items-center gap-2 text-[12.5px] font-semibold" style={{ color: "var(--slate)" }}>
            <input type="checkbox" checked={flaggedOnly} onChange={(e) => setFlaggedOnly(e.target.checked)} />
            Flagged only
          </label>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm" style={{ minWidth: 560 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                <th className="text-left pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Facility</th>
                <th className="text-left pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>State</th>
                <th className="text-left pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Cluster</th>
                <th className="text-right pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>HAI Mean Score</th>
                <th className="text-right pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Anomaly Score</th>
              </tr>
            </thead>
            <tbody>
              {data.hospitals.map((h) => (
                <tr key={h["Facility ID"]} style={{ borderBottom: "1px solid var(--border-soft)" }}>
                  <td className="py-3 text-[12.5px] font-bold" style={{ color: "var(--ink)" }}>{h["Facility Name"]}</td>
                  <td className="py-3 text-[12.5px] font-medium" style={{ color: "var(--slate)" }}>{h.State}</td>
                  <td className="py-3">
                    <span
                      className="inline-flex px-2.5 py-1 rounded-full text-[10.5px] font-bold uppercase"
                      style={{
                        background: h.cluster_name.includes("Stronger") ? "var(--savings-bg)" : "var(--loss-bg)",
                        color: h.cluster_name.includes("Stronger") ? "var(--savings)" : "var(--loss)",
                      }}
                    >
                      {h.cluster_name}
                    </span>
                  </td>
                  <td className="py-3 text-[12.5px] font-mono text-right" style={{ color: "var(--ink)" }}>{h.HAI_mean_score.toFixed(2)}</td>
                  <td className="py-3 text-[12.5px] font-mono text-right" style={{ color: "var(--ink)" }}>{h.anomaly_score.toFixed(3)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
