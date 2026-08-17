const BASE = "/api";

export interface DashboardData {
  kpis: {
    total_acos: number;
    savings_acos: number;
    loss_acos: number;
    total_net_savings_loss: number;
    avg_quality: number;
    anomalous_aco_count: number;
    avg_contract_health: number;
    avg_ml_risk: number;
  };
  cluster_distribution: Record<string, number>;
  financial_quality_bubbles: {
    aco_id: string;
    name: string;
    financial_pct: number;
    quality: number;
    anomaly: string;
    contract_health_score: number;
  }[];
  top_opportunities: {
    priority_rank: number;
    ACO_ID: string;
    ACO_Name: string;
    opportunity_priority: number;
    driver_name: string;
    financial_status: string;
    confidence: string;
  }[];
}

export interface AcoSummary {
  ACO_ID: string;
  ACO_Name: string;
  financial_status: string;
  GenSaveLoss: number;
  QualScore: number;
  quality_band: string;
  confidence_tier: string;
  contract_health_score: number;
}

export interface AcoDetail {
  aco_id: string;
  aco_name: string;
  financial: {
    status: string;
    gen_save_loss: number;
    expenditure_gap_pct: number;
    peer_group: string;
    peer_group_widened: boolean;
  };
  quality: { score: number; band: string; peer_percentile: number };
  ml_profile: { cluster: string; anomaly_score: number; confidence_tier: string };
  scores: {
    contract_health: number;
    ml_risk: number;
    breakdown: {
      financial_subscore: number;
      quality_subscore: number;
      utilization_subscore: number;
      ml_risk_score: number;
      weights: Record<string, number>;
      trend_status: string;
    };
    disclosure: string;
  };
}

export interface UtilizationMetric {
  metric: string;
  value: number;
  peer_median: number | null;
  deviation_pct: number | null;
  percentile: number | null;
}

export interface HospitalSummary {
  "Facility ID": number;
  "Facility Name": string;
  State: string;
  cluster_name: string;
  HAI_mean_score: number;
  anomaly_score: number;
  is_high_confidence_anomaly: boolean;
}

export interface HospitalDetail extends HospitalSummary {
  attribution_note: string;
}

export interface Contract {
  aco_id: string;
  aco_name: string;
  peer_group: string;
  peer_group_size: number;
  benchmark: number;
  actual_expenditure: number;
  expenditure_gap_pct: number;
  gross_savings_loss: number;
  earned_savings_loss: number;
  share_rate: number;
  loss_rate: number;
  financial_status: string;
  quality_score: number;
  quality_band: string;
  contract_health_score: number;
  utilization_score: number;
  ml_risk_score: number;
  confidence_tier: string;
}

export interface ContractsResponse {
  contracts: Contract[];
  total_contracts: number;
  portfolio_avg_contract_health: number;
  portfolio_avg_quality: number;
  portfolio_avg_utilization: number;
  portfolio_total_benchmark: number;
  portfolio_total_expenditure: number;
  portfolio_total_gross_savings_loss: number;
  portfolio_total_earned_savings_loss: number;
}

export interface DriverCandidate {
  ACO_ID: string;
  driver_name: string;
  driver_metric: string;
  peer_percentile: number;
  driver_score: number;
  component_raw_deviation: number;
  component_pca_strength: number;
  component_anomaly_strength: number;
  component_financial_relevance: number;
  component_quality_relevance: number;
  component_confidence: number;
  confidence_label: string;
}

export interface AskResponse {
  question: string;
  answer: string | null;
  status: "ok" | "unavailable" | "validation_failed";
  reason: string | null;
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

export const api = {
  dashboard: () => get<DashboardData>("/dashboard"),
  acos: () => get<AcoSummary[]>("/acos"),
  aco: (id: string) => get<AcoDetail>(`/acos/${id}`),
  acoUtilization: (id: string) => get<{ aco_id: string; metrics: UtilizationMetric[] }>(`/acos/${id}/utilization`),
  acoDrivers: (id: string) => get<DriverCandidate[]>(`/acos/${id}/drivers`),
  acoMlProfile: (id: string) => get<any>(`/acos/${id}/ml-profile`),
  acoAnomalies: (id: string) => get<any>(`/acos/${id}/anomalies`),
  opportunities: (limit = 50) => get<any[]>(`/opportunities?limit=${limit}`),
  hospitals: (limit = 500) => get<{ hospitals: HospitalSummary[] }>(`/hospitals?flagged_only=false&limit=${limit}`),
  hospital: (id: string | number) => get<HospitalDetail>(`/hospitals/${id}`),
  contracts: () => get<ContractsResponse>("/contracts"),
  reviewBrief: (id: string) =>
    fetch(`${BASE}/acos/${id}/review-brief`, { method: "POST" }).then((r) => r.json()),
  askAboutAco: (id: string, question: string) =>
    fetch(`${BASE}/acos/${id}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }).then(async (r) => {
      if (!r.ok) throw new Error(`API error ${r.status}: /acos/${id}/ask`);
      return r.json() as Promise<AskResponse>;
    }),
};
