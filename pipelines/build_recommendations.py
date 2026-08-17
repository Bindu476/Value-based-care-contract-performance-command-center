"""
pipelines/build_recommendations.py — Phase 11, SRS Section 16.
Deterministic, rule-based. Never LLM-generated. Rules A-C operate at ACO grain (data available).
Rules D-E operate at provider grain (structural proof-of-concept on synthetic sample — see
Phase 8 caveat). Rule F operates at portfolio grain, since no ACO-hospital attribution exists
(Section 3.4) — it cannot honestly fire "for this ACO", only as general portfolio context.
"""

import sys as _sys
from pathlib import Path as _Path
_p = _Path(__file__).resolve()
while not (_p / "paths.py").exists():
    _p = _p.parent
_sys.path.insert(0, str(_p))
from paths import PROJECT_ROOT

import pandas as pd


def load_aco_inputs():
    fin = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/financial_scorecard.parquet")
    util = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/utilization_scorecard.parquet")
    cluster = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/aco_cluster_assignments.parquet")[["ACO_ID", "cluster", "utilization_PC1"]]
    anomaly = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/aco_anomaly_scores.parquet")
    return fin.merge(util, on="ACO_ID").merge(cluster, on="ACO_ID").merge(anomaly, on="ACO_ID")


def apply_aco_rules(df):
    records = []

    # Rule A: Financial=LOSS AND acute utilization>P90 AND acute PCA component high
    utilization_pc1_high = df["utilization_PC1"] > df["utilization_PC1"].quantile(0.75)
    acute_p90 = (df.get("ADM_percentile", pd.Series(0, index=df.index)) > 90) | \
                (df.get("P_EDV_Vis_percentile", pd.Series(0, index=df.index)) > 90)
    rule_a = df[(df.financial_status == "LOSS") & acute_p90 & utilization_pc1_high]
    for _, r in rule_a.iterrows():
        records.append({"ACO_ID": r.ACO_ID, "rule": "A", "recommendation": "Review acute-care utilization",
                         "evidence": f"LOSS status, acute utilization elevated, high acute PCA loading"})

    # Rule C: SNF utilization>P90 OR SNF LOS>P90
    snf_p90 = (df.get("P_SNF_ADM_percentile", pd.Series(0, index=df.index)) > 90) | \
              (df.get("SNF_LOS_percentile", pd.Series(0, index=df.index)) > 90)
    rule_c = df[snf_p90]
    for _, r in rule_c.iterrows():
        records.append({"ACO_ID": r.ACO_ID, "rule": "C", "recommendation": "Review post-acute transitions",
                         "evidence": f"SNF utilization or length-of-stay above 90th percentile vs peers"})

    return pd.DataFrame(records)


def apply_provider_rules():
    """Rules D-E: provider-grain, structural proof-of-concept per Phase 8 caveat."""
    prov = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/provider_ml_results.parquet")
    cost_p75 = prov["avg_payment_per_beneficiary"].quantile(0.75)
    cost_p25 = prov["avg_payment_per_beneficiary"].quantile(0.25)
    # no independent provider-quality metric available in this source (Section 7.3 of provider ML) —
    # using anomaly flag as the "requires review" proxy for D, and cluster membership as a service-pattern proxy for E
    records = []
    rule_d = prov[(prov["avg_payment_per_beneficiary"] > cost_p75) & (prov["is_high_confidence_anomaly"])]
    for _, r in rule_d.iterrows():
        records.append({"NPI": r.Rndrng_NPI, "rule": "D", "recommendation": "High-priority provider review",
                         "evidence": "High cost per beneficiary + flagged as statistical anomaly",
                         "caveat": "Structural proof-of-concept on synthetic sample — rerun on real physician data"})
    rule_e = prov[(prov["avg_payment_per_beneficiary"] < cost_p25) & (~prov["is_high_confidence_anomaly"])]
    for _, r in rule_e.iterrows():
        records.append({"NPI": r.Rndrng_NPI, "rule": "E", "recommendation": "Best-practice candidate",
                         "evidence": "Low cost per beneficiary, not flagged as anomalous",
                         "caveat": "Structural proof-of-concept on synthetic sample — rerun on real physician data"})
    return pd.DataFrame(records)


def apply_hospital_rule():
    """Rule F: portfolio-grain only — no ACO attribution exists (Section 3.4)."""
    hosp = pd.read_parquet(f"{PROJECT_ROOT}/data/analytical/hospital_ml_results.parquet")
    flagged = hosp[hosp.is_high_confidence_anomaly]
    return pd.DataFrame({
        "rule": ["F"], "recommendation": ["Review hospital safety performance (national context)"],
        "n_facilities_flagged": [len(flagged)],
        "evidence": [f"{len(flagged)} facilities show statistically unusual safety profiles vs national peers"],
        "caveat": ["Not attributed to any specific ACO — no verified ACO-hospital crosswalk exists (Section 3.4)"]
    })


if __name__ == "__main__":
    aco_df = load_aco_inputs()
    aco_recs = apply_aco_rules(aco_df)
    provider_recs = apply_provider_rules()
    hospital_rec = apply_hospital_rule()

    aco_recs.to_csv(f"{PROJECT_ROOT}/data/analytical/recommendations_aco.csv", index=False)
    provider_recs.to_csv(f"{PROJECT_ROOT}/data/analytical/recommendations_provider.csv", index=False)
    hospital_rec.to_csv(f"{PROJECT_ROOT}/data/analytical/recommendations_hospital.csv", index=False)

    print(f"Rule A (acute utilization + loss) triggered: {(aco_recs.rule=='A').sum()} ACOs")
    print(f"Rule C (SNF utilization/LOS) triggered: {(aco_recs.rule=='C').sum()} ACOs")
    print(f"Rule D (high-priority provider) triggered: {(provider_recs.rule=='D').sum()} providers [sample-scale]")
    print(f"Rule E (best-practice candidate) triggered: {(provider_recs.rule=='E').sum()} providers [sample-scale]")
    print(f"\nRule F (hospital safety, portfolio-level):")
    print(hospital_rec.to_string(index=False))

    print("\nSample Rule A/C triggers:")
    print(aco_recs.head(5).to_string(index=False))
