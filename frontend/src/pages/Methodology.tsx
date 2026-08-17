import { Link } from "react-router-dom";

const LIMITATIONS = [
  "MSSP data is ACO-level, not patient-level.",
  "Physician data is provider/service-level.",
  "HVBP data is hospital-level.",
  "Direct ACO-provider or ACO-hospital attribution may not be available; no fake joins are made.",
  "ML identifies statistical patterns, not causality.",
  "PCA components are latent statistical constructs, application-labeled from loadings.",
  "Clusters are application-generated profiles, not CMS classifications.",
  "Anomaly does not mean poor performance.",
  "A recommendation does not guarantee savings.",
  "Application-defined scores (Contract Health, ML Risk) are not CMS scores.",
  "CMS attribution methodology is not reconstructed.",
  "CMS benchmark methodology is not reconstructed.",
  "Small-sample caveat: 476 ACO records — cluster/anomaly outputs validated via seed-stability checks.",
  "Single performance year — no true multi-year trend; Trend component inactive.",
  "Composite scores are unvalidated against any ground truth — no labeled outcome exists to check against.",
  "Isolation Forest explanations are peer-deviation-based, not native feature importances.",
];

const GLOSSARY = [
  ["ACO", "Accountable Care Organization — providers sharing responsibility for a patient population's cost and quality."],
  ["MSSP", "Medicare Shared Savings Program — CMS's main ACO value-based care program."],
  ["HCC", "Hierarchical Condition Category — basis for CMS risk scoring."],
  ["NPI", "National Provider Identifier — unique ID per billing provider."],
  ["HCPCS", "Healthcare Common Procedure Coding System — billing codes for services."],
  ["HVBP", "Hospital Value-Based Purchasing — CMS hospital quality payment program."],
  ["HAI", "Hospital-Acquired Infection."],
  ["SEP-1", "Severe Sepsis and Septic Shock Management measure."],
  ["CAHPS", "Consumer Assessment of Healthcare Providers and Systems — patient experience survey."],
  ["PCA", "Principal Component Analysis — dimensionality reduction technique."],
  ["RUCA", "Rural-Urban Commuting Area code — rurality classification."],
];

export default function Methodology() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-10">
      <Link to="/" className="text-sm" style={{ color: "var(--slate)" }}>← Command Center</Link>
      <h1 className="font-display text-3xl font-semibold mt-3 mb-2">Methodology &amp; Limitations</h1>
      <p className="text-sm mb-8" style={{ color: "var(--slate)" }}>
        Read this before acting on anything in this application. It explains what the ML actually does,
        and what it deliberately does not claim.
      </p>

      <section className="mb-8">
        <h2 className="font-display text-xl font-semibold mb-3">How this works</h2>
        <p className="text-sm mb-3">
          Three CMS public datasets — MSSP ACO results, Physician &amp; Other Practitioners by Provider and Service,
          and Hospital VBP Safety — do not share a grain. An ACO's data covers a whole contract population; provider
          data is per billing NPI nationwide; hospital data is per facility. <strong>This application never fabricates
          a join between them.</strong> Provider and hospital findings are shown as national context, never as
          "this provider caused this ACO's result."
        </p>
        <p className="text-sm mb-3">
          For each dataset, raw variables go through PCA to find latent patterns, KMeans clustering to group
          similar entities, and Isolation Forest to flag statistical outliers — validated by re-running with
          multiple random seeds and keeping only findings that are stable across reruns.
        </p>
        <p className="text-sm">
          Every ML finding is explained by comparing the flagged entity's raw metrics against its peer group,
          in plain language — never a bare score with no context.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="font-display text-xl font-semibold mb-3">Limitations</h2>
        <ul className="text-sm space-y-1.5 list-disc list-inside" style={{ color: "var(--slate)" }}>
          {LIMITATIONS.map((l, i) => <li key={i}>{l}</li>)}
        </ul>
      </section>

      <section>
        <h2 className="font-display text-xl font-semibold mb-3">Glossary</h2>
        <dl className="text-sm grid gap-2">
          {GLOSSARY.map(([term, def]) => (
            <div key={term} className="flex gap-3">
              <dt className="font-mono font-semibold w-20 shrink-0">{term}</dt>
              <dd style={{ color: "var(--slate)" }}>{def}</dd>
            </div>
          ))}
        </dl>
      </section>
    </div>
  );
}
