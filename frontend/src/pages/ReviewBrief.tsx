import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../services/api";
import ScoreBreakdownCard from "../components/ScoreBreakdownCard";

export default function ReviewBrief() {
  const { acoId } = useParams<{ acoId: string }>();
  const [brief, setBrief] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!acoId) return;
    api.reviewBrief(acoId).then((b) => {
      setBrief(b);
      setLoading(false);
    });
  }, [acoId]);

  if (loading) return <div className="p-8" style={{ color: "var(--slate)" }}>Generating review brief...</div>;
  if (!brief) return <div className="p-8" style={{ color: "var(--loss)" }}>Could not generate brief.</div>;

  return (
    <div className="max-w-3xl mx-auto px-6 py-10 print:py-0">
      <div className="flex justify-between items-center mb-6 print:hidden">
        <Link to={`/acos/${acoId}`} className="text-sm" style={{ color: "var(--slate)" }}>← ACO Detail</Link>
        <button
          onClick={() => window.print()}
          className="px-4 py-2 rounded-xl text-sm font-medium"
          style={{ background: "var(--accent)", color: "white" }}
        >
          Print / Export
        </button>
      </div>

      <div className="rounded-xl border p-8" style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}>
        <header className="mb-6 pb-4 border-b" style={{ borderColor: "var(--border)" }}>
          <p className="text-xs uppercase tracking-wide" style={{ color: "var(--slate)" }}>Provider Review Brief</p>
          <h1 className="font-display text-2xl font-semibold mt-1">{brief.aco_name}</h1>
          <p className="font-mono text-xs mt-1" style={{ color: "var(--slate-light)" }}>{brief.aco_id}</p>
        </header>

        <section className="mb-6">
          <h2 className="font-display text-lg font-semibold mb-2">Executive Summary</h2>
          {brief.narrative_status === "ok" ? (
            <p className="text-sm leading-relaxed">{brief.narrative}</p>
          ) : (
            <div
              className="text-xs p-3 rounded border"
              style={{ borderColor: "var(--anomaly)", background: "var(--anomaly-bg)", color: "var(--ink)" }}
            >
              <strong>Narrative generation unavailable — showing structured data below.</strong>
              {brief.narrative_note && <div className="mt-1 font-mono">{brief.narrative_note}</div>}
            </div>
          )}
        </section>

        <section className="mb-6">
          <ScoreBreakdownCard
            title="Contract Health"
            score={brief.contract_health.contract_health}
            disclosure={brief.contract_health.disclosure}
            components={[
              { label: "Financial", value: brief.contract_health.breakdown.financial_subscore, weight: brief.contract_health.breakdown.weights.financial },
              { label: "Quality", value: brief.contract_health.breakdown.quality_subscore, weight: brief.contract_health.breakdown.weights.quality },
              { label: "Utilization", value: brief.contract_health.breakdown.utilization_subscore, weight: brief.contract_health.breakdown.weights.utilization },
              { label: "ML Risk (inverted)", value: 100 - brief.contract_health.breakdown.ml_risk_score, weight: brief.contract_health.breakdown.weights.ml_risk },
            ]}
          />
        </section>

        <section className="mb-6">
          <h2 className="font-display text-lg font-semibold mb-2">Financial Performance</h2>
          <p className="text-sm">
            This ACO recorded a <strong style={{ color: brief.financial.status === "LOSS" ? "var(--loss)" : "var(--savings)" }}>
              {brief.financial.status}
            </strong> of ${Math.abs(brief.financial.gross_savings_loss).toLocaleString()} against a benchmark of
            ${brief.financial.benchmark.toLocaleString()} (actual expenditure ${brief.financial.actual_expenditure.toLocaleString()},
            a gap of {brief.financial.expenditure_gap_pct}%).
          </p>
        </section>

        <section className="mb-6">
          <h2 className="font-display text-lg font-semibold mb-2">Quality</h2>
          <p className="text-sm">
            Quality score of {brief.quality.score} places this ACO at the {brief.quality.peer_percentile}th percentile
            among peers — banded as <strong>{brief.quality.band}</strong>.
          </p>
        </section>

        <section className="mb-6">
          <h2 className="font-display text-lg font-semibold mb-2">ML-Detected Pattern</h2>
          <p className="text-sm mb-2">
            This ACO's utilization/financial profile places it in the <strong>{brief.ml.cluster}</strong> segment.
            {brief.ml.confidence_tier !== "NOT FLAGGED" && (
              <> Flagged as a <strong>{brief.ml.confidence_tier}</strong> confidence statistical anomaly relative to peers.</>
            )}
          </p>
          {brief.ml.anomaly_explanation && (
            <p className="text-sm font-mono" style={{ color: "var(--slate)" }}>{brief.ml.anomaly_explanation}</p>
          )}
        </section>

        <section className="mb-6">
          <h2 className="font-display text-lg font-semibold mb-2">Top Drivers</h2>
          <ol className="text-sm space-y-1 list-decimal list-inside">
            {brief.drivers.map((d: any, i: number) => (
              <li key={i}>
                <strong>{d.name}</strong> (priority {d.priority}, {d.confidence} confidence) — {d.evidence.join("; ")}
              </li>
            ))}
          </ol>
        </section>

        <section className="mb-6">
          <h2 className="font-display text-lg font-semibold mb-2">Recommended Actions</h2>
          <ul className="text-sm space-y-1 list-disc list-inside">
            {brief.recommendations.map((r: string, i: number) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </section>

        <section className="mb-6 text-xs p-3 rounded" style={{ background: "var(--paper)", color: "var(--slate)" }}>
          <strong>Context (national, not attributed to this ACO):</strong> {brief.hospital_context.n_facilities_flagged_nationally} hospital
          facilities nationally show unusual safety profiles. {brief.providers.note}
        </section>

        <footer className="pt-4 border-t text-xs" style={{ borderColor: "var(--border)", color: "var(--slate-light)" }}>
          <strong>Limitations:</strong>
          <ul className="list-disc list-inside mt-1 space-y-0.5">
            {brief.limitations.map((l: string, i: number) => <li key={i}>{l}</li>)}
          </ul>
        </footer>
      </div>
    </div>
  );
}
