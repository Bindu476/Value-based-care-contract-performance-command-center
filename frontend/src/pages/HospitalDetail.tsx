import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { api, type HospitalDetail as HospitalDetailType } from "../services/api";

export default function HospitalDetail() {
  const { hospitalId } = useParams<{ hospitalId: string }>();
  const [hospital, setHospital] = useState<HospitalDetailType | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!hospitalId) return;
    api.hospital(hospitalId).then(setHospital).catch((e) => setError(String(e)));
  }, [hospitalId]);

  if (error) return <div className="p-8 font-mono text-sm" style={{ color: "var(--loss)" }}>{error}</div>;
  if (!hospital) return <div className="p-8" style={{ color: "var(--slate)" }}>Loading facility profile...</div>;

  const isStronger = hospital.cluster_name.includes("Stronger");

  return (
    <div className="max-w-4xl mx-auto px-7 py-8">
      <Link to="/hospitals" className="text-[12.5px] font-semibold" style={{ color: "var(--slate-light)" }}>← Hospital Quality</Link>

      <header className="mt-3 mb-6">
        <h1 className="font-display text-[19px]" style={{ color: "var(--ink)" }}>{hospital["Facility Name"]}</h1>
        <p className="font-mono text-xs mt-1" style={{ color: "var(--slate-light)" }}>
          Facility ID {hospital["Facility ID"]} · {hospital.State}
        </p>
      </header>

      <div
        className="rounded-xl border p-3.5 mb-5 text-xs font-medium"
        style={{ borderColor: "var(--border)", background: "var(--paper-raised)", color: "var(--slate)", boxShadow: "var(--glass-shadow)" }}
      >
        {hospital.attribution_note}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-3.5 mb-5">
        <div className="rounded-xl border p-4" style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}>
          <span className="block text-[11px] font-bold uppercase tracking-wide mb-2" style={{ color: "var(--slate-light)" }}>HAI Mean Score</span>
          <span className="font-mono text-[25px] font-bold" style={{ color: "var(--ink)" }}>{hospital.HAI_mean_score.toFixed(2)}</span>
        </div>
        <div className="rounded-xl border p-4" style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}>
          <span className="block text-[11px] font-bold uppercase tracking-wide mb-2" style={{ color: "var(--slate-light)" }}>Anomaly Score</span>
          <span className="font-mono text-[25px] font-bold" style={{ color: hospital.is_high_confidence_anomaly ? "var(--anomaly)" : "var(--ink)" }}>
            {hospital.anomaly_score.toFixed(3)}
          </span>
        </div>
        <div className="rounded-xl border p-4" style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}>
          <span className="block text-[11px] font-bold uppercase tracking-wide mb-2" style={{ color: "var(--slate-light)" }}>Confidence</span>
          <span className="font-mono text-[25px] font-bold" style={{ color: "var(--ink)" }}>
            {hospital.is_high_confidence_anomaly ? "Flagged" : "—"}
          </span>
        </div>
      </div>

      <section className="rounded-xl border p-5" style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}>
        <h2 className="text-[13.5px] font-bold mb-3" style={{ color: "var(--ink)" }}>Safety Cluster</h2>
        <span
          className="inline-flex px-3 py-1.5 rounded-full text-[11px] font-bold uppercase mb-3"
          style={{ background: isStronger ? "var(--savings-bg)" : "var(--loss-bg)", color: isStronger ? "var(--savings)" : "var(--loss)" }}
        >
          {hospital.cluster_name}
        </span>
        <p className="text-[13px]" style={{ color: "var(--slate)" }}>
          This facility's HVBP safety profile places it in the <strong>{hospital.cluster_name}</strong> segment, identified via
          PCA + KMeans clustering across the national hospital portfolio.
          {hospital.is_high_confidence_anomaly && (
            <> Its safety profile is also flagged as a high-confidence statistical outlier relative to peers — this reflects
            an unusual pattern, not automatically poor performance.</>
          )}
        </p>
      </section>
    </div>
  );
}
