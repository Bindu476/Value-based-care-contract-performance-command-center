import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from "recharts";
import KPICard from "../components/KPICard";

const tipStyle = { background: "#101B33", color: "#D6E0F0" };

interface Provider {
  Rndrng_NPI: number;
  specialty: string;
  state: string;
  total_services: number;
  total_beneficiaries: number;
  avg_payment_per_beneficiary: number;
  cluster: number;
  anomaly_score: number;
  is_high_confidence_anomaly: boolean;
}

interface Stats {
  total_providers: number;
  flagged_count: number;
  flagged_pct: number;
  anomaly_score: { mean: number; std: number; min: number; max: number; p50: number; p90: number; p99: number };
  histogram: { bin_start: number; bin_end: number; count: number }[];
  cluster_distribution: Record<string, number>;
}

type SortBy = "mixed" | "anomaly_desc" | "anomaly_asc" | "npi";

export default function ProviderVariation() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [isSample, setIsSample] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [sortBy, setSortBy] = useState<SortBy>("mixed");
  const [anomaliesOnly, setAnomaliesOnly] = useState(false);
  const pageSize = 100;

  // full-dataset stats — fetched once, independent of pagination, this is the "complete
  // information" view (mean/std/percentiles/histogram over ALL rows, not just the current page)
  useEffect(() => {
    fetch("/api/providers/stats").then((r) => r.json()).then(setStats);
  }, []);

  useEffect(() => {
    const params = new URLSearchParams({
      page: String(page), page_size: String(pageSize), sort_by: sortBy,
      anomalies_only: String(anomaliesOnly),
    });
    fetch(`/api/providers?${params}`)
      .then((r) => r.json())
      .then((d) => {
        setProviders(d.providers);
        setIsSample(d.is_sample_scale);
        setTotalPages(d.total_pages);
      });
  }, [page, sortBy, anomaliesOnly]);

  return (
    <div className="max-w-6xl mx-auto px-7 py-8">
      <Link to="/" className="text-[12.5px] font-semibold" style={{ color: "var(--slate-light)" }}>← Command Center</Link>
      <h1 className="font-display text-[19px] mt-3 mb-4" style={{ color: "var(--ink)" }}>Provider Variation</h1>

      {isSample && (
        <div className="rounded-xl border p-3.5 mb-4 text-[12.5px] font-medium" style={{ borderColor: "#F1E0B6", background: "var(--anomaly-bg)", color: "var(--ink)" }}>
          <strong>Sample-scale demonstration.</strong> Rerun on the real physician file for production segmentation.
        </div>
      )}

      <div
        className="rounded-xl border p-3.5 mb-5 text-xs font-medium"
        style={{ borderColor: "var(--border)", background: "var(--paper-raised)", color: "var(--slate)", boxShadow: "var(--glass-shadow)" }}
      >
        National context only — providers shown here are <strong>not attributed to any specific ACO</strong>.
        No verified ACO-provider crosswalk exists in this dataset (Section 3.4/8.6).
      </div>

      {stats && (
        <>
          <section className="grid grid-cols-2 md:grid-cols-4 gap-3.5 mb-5">
            <KPICard label="Total Providers" value={stats.total_providers.toLocaleString()} />
            <KPICard label="Flagged Anomalies" value={`${stats.flagged_count.toLocaleString()} (${stats.flagged_pct}%)`} tone="anomaly" />
            <KPICard label="Median Score" value={stats.anomaly_score.p50.toFixed(3)} />
            <KPICard label="99th Percentile" value={stats.anomaly_score.p99.toFixed(3)} />
          </section>

          <section className="rounded-xl border p-5 mb-5" style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}>
            <h2 className="text-[13px] font-bold" style={{ color: "var(--ink)" }}>Anomaly Score Distribution — Full Dataset</h2>
            <p className="text-[11px] mt-0.5 mb-3 font-medium" style={{ color: "var(--slate-light)" }}>
              All {stats.total_providers.toLocaleString()} providers nationally, not just the current page.
              Mean {stats.anomaly_score.mean.toFixed(3)}, std {stats.anomaly_score.std.toFixed(3)}.
            </p>
            <div style={{ width: "100%", height: 260 }}>
              <ResponsiveContainer width="100%" height="100%" minWidth={280} debounce={50}>
                <BarChart data={stats.histogram} margin={{ top: 5, right: 15, bottom: 5, left: -10 }}>
                  <CartesianGrid stroke="#EEF1F7" vertical={false} />
                  <XAxis dataKey="bin_start" tickFormatter={(v) => Number(v).toFixed(2)} tick={{ fontSize: 10, fill: "#8993AC" }} axisLine={{ stroke: "#EEF1F7" }} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: "#8993AC" }} axisLine={{ stroke: "#EEF1F7" }} tickLine={false} />
                  <Tooltip
                    contentStyle={tipStyle}
                    itemStyle={{ color: "#D6E0F0" }}
                    labelStyle={{ color: "#fff", fontWeight: 600 }}
                    formatter={(v: any) => [`${v} providers`, "Count"]}
                    labelFormatter={(label) => `score ≈ ${Number(label).toFixed(2)}`}
                  />
                  <Bar dataKey="count" fill="#B4720A" radius={[3, 3, 0, 0]} isAnimationActive={false} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>
        </>
      )}

      <section className="rounded-xl border p-5" style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}>
        <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
          <h2 className="text-[13.5px] font-bold" style={{ color: "var(--ink)" }}>Browse Providers</h2>
          <div className="flex gap-3 items-center">
            <label className="flex items-center gap-2 text-[12.5px] font-semibold" style={{ color: "var(--slate)" }}>
              <input type="checkbox" checked={anomaliesOnly} onChange={(e) => { setAnomaliesOnly(e.target.checked); setPage(1); }} />
              Anomalies only
            </label>
            <select
              value={sortBy}
              onChange={(e) => { setSortBy(e.target.value as SortBy); setPage(1); }}
              className="text-[12px] font-semibold rounded-lg px-2.5 py-1.5 outline-none"
              style={{ border: "1px solid var(--border)", background: "var(--surface-2)", color: "var(--slate)" }}
            >
              <option value="mixed">Mixed (default, unbiased sample)</option>
              <option value="anomaly_desc">Highest anomaly score first</option>
              <option value="anomaly_asc">Lowest anomaly score first</option>
              <option value="npi">By NPI</option>
            </select>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm" style={{ minWidth: 640 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                <th className="text-left pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>NPI</th>
                <th className="text-left pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Specialty</th>
                <th className="text-left pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>State</th>
                <th className="text-right pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>$/Beneficiary</th>
                <th className="text-right pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Anomaly Score</th>
                <th className="text-left pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {providers.map((p) => (
                <tr key={p.Rndrng_NPI} style={{ borderBottom: "1px solid var(--border-soft)" }}>
                  <td className="py-3 text-[12.5px] font-mono" style={{ color: "var(--ink)" }}>{p.Rndrng_NPI}</td>
                  <td className="py-3 text-[12.5px] font-bold" style={{ color: "var(--ink)" }}>{p.specialty}</td>
                  <td className="py-3 text-[12.5px] font-medium" style={{ color: "var(--slate)" }}>{p.state}</td>
                  <td className="py-3 text-[12.5px] font-mono text-right" style={{ color: "var(--ink)" }}>${p.avg_payment_per_beneficiary.toFixed(0)}</td>
                  <td className="py-3 text-[12.5px] font-mono text-right" style={{ color: "var(--ink)" }}>{p.anomaly_score.toFixed(3)}</td>
                  <td className="py-3">
                    {p.is_high_confidence_anomaly ? (
                      <span className="inline-flex px-2.5 py-1 rounded-full text-[10.5px] font-bold uppercase" style={{ background: "var(--loss-bg)", color: "var(--loss)" }}>Flagged</span>
                    ) : (
                      <span className="text-[11.5px] font-medium" style={{ color: "var(--slate-light)" }}>—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between mt-4 text-[12px] font-medium" style={{ color: "var(--slate)" }}>
          <span>Page {page} of {totalPages.toLocaleString()}</span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="px-3 py-1.5 rounded-lg text-[12px] font-bold disabled:opacity-40"
              style={{ border: "1px solid var(--border)", background: "var(--surface-2)", color: "var(--slate)" }}
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1.5 rounded-lg text-[12px] font-bold disabled:opacity-40"
              style={{ border: "1px solid var(--border)", background: "var(--surface-2)", color: "var(--slate)" }}
            >
              Next
            </button>
          </div>
        </div>
      </section>
    </div>
  );
}
