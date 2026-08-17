import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, type AcoDetail as AcoDetailType, type UtilizationMetric, type DriverCandidate } from "../services/api";
import ScoreBreakdownCard from "../components/ScoreBreakdownCard";
import MLBadge from "../components/MLBadge";
import AIInsightsPanel from "../components/AIInsightsPanel";

const statusColor = (status: string) => (status === "LOSS" ? "var(--loss)" : "var(--savings)");
const tierColor = (tier: string) =>
  tier === "VERY HIGH" ? "var(--loss)" : tier === "HIGH" ? "var(--anomaly)" : "var(--slate-light)";

function PercentileBar({ value }: { value: number | null }) {
  if (value === null) return <span className="text-xs" style={{ color: "var(--slate-light)" }}>—</span>;
  const color = value >= 90 ? "var(--loss)" : value >= 75 ? "var(--anomaly)" : "var(--slate-light)";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 rounded-full" style={{ background: "var(--border)" }}>
        <div className="h-1.5 rounded-full" style={{ width: `${value}%`, background: color }} />
      </div>
      <span className="font-mono text-xs w-10 text-right">{value.toFixed(0)}th</span>
    </div>
  );
}

export default function AcoDetail() {
  const { acoId } = useParams<{ acoId: string }>();
  const [aco, setAco] = useState<AcoDetailType | null>(null);
  const [utilization, setUtilization] = useState<UtilizationMetric[]>([]);
  const [drivers, setDrivers] = useState<DriverCandidate[]>([]);
  const [tab, setTab] = useState<"overview" | "utilization" | "ml" | "drivers">("overview");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!acoId) return;
    Promise.all([api.aco(acoId), api.acoUtilization(acoId), api.acoDrivers(acoId)])
      .then(([a, u, d]) => {
        setAco(a);
        setUtilization(u.metrics);
        setDrivers(d.sort((a, b) => b.driver_score - a.driver_score));
      })
      .catch((e) => setError(String(e)));
  }, [acoId]);

  if (error) return <div className="p-8 font-mono text-sm" style={{ color: "var(--loss)" }}>{error}</div>;
  if (!aco) return <div className="p-8" style={{ color: "var(--slate)" }}>Loading ACO profile...</div>;

  return (
    <div className="max-w-6xl mx-auto px-6 py-10">
      <Link to="/" className="text-sm" style={{ color: "var(--slate)" }}>
        ← Command Center
      </Link>

      <header className="mt-3 mb-6 flex items-start justify-between flex-wrap gap-3">
        <div>
          <h1 className="font-display text-[19px]" style={{ color: "var(--ink)" }}>{aco.aco_name}</h1>
          <p className="font-mono text-xs mt-1" style={{ color: "var(--slate-light)" }}>{aco.aco_id}</p>
        </div>
        <div className="flex gap-2 flex-wrap items-center">
          <Link
            to={`/acos/${aco.aco_id}/review-brief`}
            className="px-3.5 py-1.5 rounded-lg text-xs font-bold border"
            style={{ borderColor: "var(--border)", color: "var(--ink)", background: "var(--paper-raised)" }}
          >
            Generate Review Brief
          </Link>
          <span
            className="px-2.5 py-1 rounded-full text-[10.5px] font-bold uppercase"
            style={{ background: aco.financial.status === "LOSS" ? "var(--loss-bg)" : "var(--savings-bg)", color: statusColor(aco.financial.status) }}
          >
            {aco.financial.status}
          </span>
          {aco.ml_profile.confidence_tier !== "NOT FLAGGED" && (
            <span
              className="px-2.5 py-1 rounded-full text-[10.5px] font-bold uppercase"
              style={{ background: aco.ml_profile.confidence_tier === "VERY HIGH" ? "var(--loss-bg)" : "var(--anomaly-bg)", color: tierColor(aco.ml_profile.confidence_tier) }}
            >
              ML Risk: {aco.ml_profile.confidence_tier}
            </span>
          )}
        </div>
      </header>

      <nav className="flex gap-1 mb-6 border-b" style={{ borderColor: "var(--border)" }}>
        {(["overview", "utilization", "ml", "drivers"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className="px-4 py-2.5 text-[13px] font-semibold capitalize -mb-px border-b-2 transition-colors"
            style={{
              borderColor: tab === t ? "var(--accent)" : "transparent",
              color: tab === t ? "var(--accent)" : "var(--slate-light)",
            }}
          >
            {t === "ml" ? "ML Profile" : t}
          </button>
        ))}
      </nav>

      {tab === "overview" && (
        <div className="grid md:grid-cols-2 gap-4">
          <ScoreBreakdownCard
            title="Contract Health"
            score={aco.scores.contract_health}
            disclosure={aco.scores.disclosure}
            components={[
              { label: "Financial", value: aco.scores.breakdown.financial_subscore, weight: aco.scores.breakdown.weights.financial },
              { label: "Quality", value: aco.scores.breakdown.quality_subscore, weight: aco.scores.breakdown.weights.quality },
              { label: "Utilization", value: aco.scores.breakdown.utilization_subscore, weight: aco.scores.breakdown.weights.utilization },
              { label: "ML Risk (inverted)", value: 100 - aco.scores.breakdown.ml_risk_score, weight: aco.scores.breakdown.weights.ml_risk },
            ]}
          />
          <div className="rounded-xl border p-5" style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}>
            <h3 className="text-[13.5px] font-bold mb-3.5" style={{ color: "var(--ink)" }}>Financial &amp; Quality</h3>
            <dl className="space-y-2.5 text-[12.5px]">
              <div className="flex justify-between">
                <dt className="font-semibold" style={{ color: "var(--slate)" }}>Gross Savings/Loss</dt>
                <dd className="font-mono font-bold" style={{ color: statusColor(aco.financial.status) }}>
                  ${aco.financial.gen_save_loss.toLocaleString()}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="font-semibold" style={{ color: "var(--slate)" }}>Expenditure Gap</dt>
                <dd className="font-mono">{aco.financial.expenditure_gap_pct.toFixed(2)}%</dd>
              </div>
              <div className="flex justify-between">
                <dt className="font-semibold" style={{ color: "var(--slate)" }}>Quality Score</dt>
                <dd className="font-mono">{aco.quality.score.toFixed(1)} ({aco.quality.band})</dd>
              </div>
              <div className="flex justify-between">
                <dt className="font-semibold" style={{ color: "var(--slate)" }}>Peer Group</dt>
                <dd className="font-mono text-xs text-right">
                  {aco.financial.peer_group}
                  {aco.financial.peer_group_widened && (
                    <div className="text-[10px] italic" style={{ color: "var(--slate-light)" }}>
                      widened comparison — small native peer group
                    </div>
                  )}
                </dd>
              </div>
            </dl>
          </div>
          <div className="md:col-span-2">
            <AIInsightsPanel acoId={aco.aco_id} />
          </div>
        </div>
      )}

      {tab === "utilization" && (
        <div className="rounded-xl border p-5" style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}>
          <h3 className="text-[13.5px] font-bold mb-4" style={{ color: "var(--ink)" }}>Utilization vs. Peers</h3>
          <div className="overflow-x-auto">
          <table className="w-full text-sm" style={{ minWidth: 560 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                <th className="text-left pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Metric</th>
                <th className="text-left pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Value</th>
                <th className="text-left pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Peer Median</th>
                <th className="text-left pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Deviation</th>
                <th className="text-left pb-2.5 text-[10px] font-bold uppercase tracking-wide w-40" style={{ color: "var(--slate-light)" }}>Percentile</th>
              </tr>
            </thead>
            <tbody>
              {utilization.map((m) => (
                <tr key={m.metric} style={{ borderBottom: "1px solid var(--border-soft)" }}>
                  <td className="py-3 text-[12.5px] font-bold" style={{ color: "var(--ink)" }}>{m.metric}</td>
                  <td className="py-3 text-[12.5px] font-mono" style={{ color: "var(--ink)" }}>{m.value.toLocaleString()}</td>
                  <td className="py-3 text-[12.5px] font-mono" style={{ color: "var(--ink)" }}>{m.peer_median?.toLocaleString() ?? "—"}</td>
                  <td className="py-3 text-[12.5px] font-mono font-bold" style={{ color: (m.deviation_pct ?? 0) > 0 ? "var(--loss)" : "var(--savings)" }}>
                    {m.deviation_pct !== null ? `${m.deviation_pct > 0 ? "+" : ""}${m.deviation_pct.toFixed(1)}%` : "—"}
                  </td>
                  <td className="py-3"><PercentileBar value={m.percentile} /></td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      )}

      {tab === "ml" && (
        <div className="rounded-xl border p-5" style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}>
          <div className="mb-4">
            <MLBadge>{aco.ml_profile.cluster}</MLBadge>
          </div>
          <p className="text-sm mb-4" style={{ color: "var(--slate)" }}>
            This ACO's utilization, financial, and risk profile places it in the <strong>{aco.ml_profile.cluster}</strong> segment,
            identified via PCA + KMeans clustering across the full portfolio (see Methodology).
          </p>
          <dl className="grid grid-cols-2 gap-4 text-sm mb-4">
            <div>
              <dt style={{ color: "var(--slate)" }}>Anomaly Score</dt>
              <dd className="font-mono text-lg">{aco.ml_profile.anomaly_score.toFixed(3)}</dd>
            </div>
            <div>
              <dt style={{ color: "var(--slate)" }}>Confidence Tier</dt>
              <dd className="font-mono text-lg" style={{ color: tierColor(aco.ml_profile.confidence_tier) }}>
                {aco.ml_profile.confidence_tier}
              </dd>
            </div>
          </dl>
          <p className="text-xs italic" style={{ color: "var(--slate-light)" }}>
            ML identifies statistical patterns, not causality. Cluster and anomaly labels are application-generated
            interpretations of the underlying data, not official CMS classifications.
          </p>
        </div>
      )}

      {tab === "drivers" && (
        <div className="space-y-3">
          {drivers.map((d) => (
            <div
              key={d.driver_metric}
              className="rounded-xl border p-4 flex items-center justify-between"
              style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}
            >
              <div>
                <div className="font-semibold text-sm">{d.driver_name}</div>
                <div className="text-xs mt-1" style={{ color: "var(--slate)" }}>
                  {d.peer_percentile.toFixed(0)}th percentile vs. peers · confidence: {d.confidence_label}
                </div>
              </div>
              <div className="font-mono text-2xl font-semibold" style={{ color: "var(--ink)" }}>
                {d.driver_score.toFixed(1)}
              </div>
            </div>
          ))}
          {drivers.length === 0 && (
            <p className="text-sm" style={{ color: "var(--slate)" }}>No driver candidates for this ACO.</p>
          )}
        </div>
      )}
    </div>
  );
}
