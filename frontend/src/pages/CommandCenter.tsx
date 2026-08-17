import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
  AreaChart, Area, PieChart, Pie, Legend,
} from "recharts";
import { api, type DashboardData } from "../services/api";
import KPICard from "../components/KPICard";

const anomalyColor: Record<string, string> = {
  "VERY HIGH": "var(--loss)",
  HIGH: "var(--anomaly)",
  "NOT FLAGGED": "#A6AFC2",
};

const DONUT_COLORS = ["#2461EA", "#0D9488", "#B4720A", "#A6AFC2"];

const chartTooltipStyle = { background: "#101B33", color: "#D6E0F0" };

function ChartCard({ title, desc, children }: { title: string; desc: string; children: React.ReactNode }) {
  return (
    <div
      className="rounded-xl border p-5"
      style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}
    >
      <h3 className="text-[13px] font-bold" style={{ color: "var(--ink)" }}>{title}</h3>
      <p className="text-[11px] mt-0.5 mb-3 font-medium" style={{ color: "var(--slate-light)" }}>{desc}</p>
      {children}
    </div>
  );
}

export default function CommandCenter() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.dashboard().then(setData).catch((e) => setError(String(e)));
  }, []);

  if (error) {
    return (
      <div className="p-8 font-mono text-sm" style={{ color: "var(--loss)" }}>
        Could not load dashboard data: {error}
        <br />
        Is the backend running at http://localhost:8000?
      </div>
    );
  }
  if (!data) return <div className="p-8" style={{ color: "var(--slate)" }}>Loading portfolio...</div>;

  const { kpis, top_opportunities, financial_quality_bubbles, cluster_distribution } = data;
  const topOpp = top_opportunities[0];

  const gapDistribution = [...financial_quality_bubbles]
    .sort((a, b) => a.financial_pct - b.financial_pct)
    .map((d, i) => ({ rank: i + 1, pct: d.financial_pct }));

  const clusterPieData = Object.entries(cluster_distribution).map(([name, value]) => ({ name, value }));
  const statusPieData = [
    { name: "Savings", value: kpis.savings_acos },
    { name: "Loss", value: kpis.loss_acos },
  ];

  return (
    <div className="max-w-7xl mx-auto px-7 py-8">
      <section className="mb-5">
        <div className="flex items-center justify-between mb-2.5 flex-wrap gap-2">
          <h2 className="text-[12px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Main Outcomes</h2>
          <span className="text-[11.5px] font-medium" style={{ color: "var(--slate-light)" }}>{kpis.total_acos} contracts · Performance Year 2024</span>
        </div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
          <KPICard
            label="Cost & Utilization Performance"
            value={`$${(kpis.total_net_savings_loss / 1e9).toFixed(2)}B`}
            sublabel={`Net savings across ${kpis.savings_acos} of ${kpis.total_acos} contracts`}
            tone="savings"
          />
          <KPICard
            label="Risk"
            value={String(kpis.anomalous_aco_count)}
            sublabel={`ML-flagged contracts · avg risk score ${kpis.avg_ml_risk.toFixed(1)}/100`}
            tone="anomaly"
          />
          <KPICard
            label="Quality"
            value={kpis.avg_quality.toFixed(1)}
            sublabel="Portfolio average quality score"
          />
          <KPICard
            label="Score"
            value={kpis.avg_contract_health.toFixed(1)}
            sublabel="Avg. Contract Health (financial + quality + utilization + ML risk)"
          />
        </div>
      </section>

      <section className="grid grid-cols-3 gap-3.5 mb-5">
        <KPICard label="Total ACOs" value={String(kpis.total_acos)} />
        <KPICard label="Savings" value={String(kpis.savings_acos)} tone="savings" />
        <KPICard label="Loss" value={String(kpis.loss_acos)} tone="loss" />
      </section>

      {topOpp && (
        <section
          className="rounded-xl p-5 mb-4"
          style={{ background: "linear-gradient(135deg, var(--accent-bg) 0%, var(--savings-bg) 100%)", border: "1px solid var(--border)" }}
        >
          <div className="flex items-center gap-2.5 mb-2.5">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center text-white text-[13px] shrink-0"
              style={{ background: "linear-gradient(135deg,#2461EA,#0D9488)" }}
            >
              ✦
            </div>
            <span className="text-[11px] font-extrabold uppercase tracking-wide" style={{ color: "var(--ink)" }}>ML-Flagged Priority</span>
          </div>
          <p className="text-[13.5px] leading-relaxed mb-3" style={{ color: "var(--slate)", maxWidth: "70ch" }}>
            <strong style={{ color: "var(--ink)" }}>{topOpp.ACO_Name}</strong> ranks highest for review this cycle — priority score{" "}
            <strong style={{ color: "var(--ink)" }}>{topOpp.opportunity_priority.toFixed(1)}</strong>, driven primarily by{" "}
            <strong style={{ color: "var(--ink)" }}>{topOpp.driver_name}</strong>, at{" "}
            <strong style={{ color: "var(--ink)" }}>{topOpp.confidence}</strong> ML confidence. This is a deterministic, rule-based
            ranking from the driver/opportunity engine — not a generative summary.
          </p>
          <Link
            to={`/acos/${topOpp.ACO_ID}/review-brief`}
            className="inline-flex items-center gap-1.5 text-[12px] font-bold px-3 py-1.5 rounded-lg text-white"
            style={{ background: "var(--accent)" }}
          >
            View grounded review brief →
          </Link>
        </section>
      )}

      <section className="grid lg:grid-cols-[1.4fr_1fr] gap-4 mb-4 items-stretch">
        <ChartCard title="Expenditure Gap Distribution" desc="All 476 ACOs, ranked and sorted by expenditure gap vs. benchmark — continuous view of portfolio spread.">
          <div style={{ width: "100%", height: 230, minWidth: 260 }}>
            <ResponsiveContainer width="100%" height="100%" minWidth={260} debounce={50}>
              <AreaChart data={gapDistribution} margin={{ top: 5, right: 15, bottom: 0, left: -10 }}>
                <defs>
                  <linearGradient id="gapFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#2461EA" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#2461EA" stopOpacity={0.02} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#EEF1F7" vertical={false} />
                <XAxis dataKey="rank" tick={{ fontSize: 10, fill: "#8993AC" }} axisLine={{ stroke: "#EEF1F7" }} tickLine={false}
                  label={{ value: "ACOs, ranked", position: "insideBottom", offset: -4, fontSize: 10.5, fill: "#8993AC" }} />
                <YAxis tick={{ fontSize: 10, fill: "#8993AC" }} axisLine={{ stroke: "#EEF1F7" }} tickLine={false}
                  label={{ value: "Gap (%)", angle: -90, position: "insideLeft", fontSize: 10.5, fill: "#8993AC" }} />
                <Tooltip contentStyle={chartTooltipStyle} labelStyle={{ color: "#fff", fontWeight: 600 }} itemStyle={{ color: "#D6E0F0" }}
                  formatter={(v: any) => [`${Number(v).toFixed(1)}%`, "Expenditure gap"]} labelFormatter={(l) => `Rank #${l}`} />
                <Area type="monotone" dataKey="pct" stroke="#2461EA" strokeWidth={2} fill="url(#gapFill)" isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </ChartCard>

        <ChartCard title="Portfolio Composition" desc="Cluster segment and financial status mix, precomputed by the ML pipeline.">
          <div className="grid grid-cols-2 gap-2">
            <div style={{ width: "100%", height: 190 }}>
              <ResponsiveContainer width="100%" height="100%" minWidth={100} debounce={50}>
                <PieChart>
                  <Tooltip contentStyle={chartTooltipStyle} itemStyle={{ color: "#D6E0F0" }} />
                  <Pie data={clusterPieData} dataKey="value" nameKey="name" cx="50%" cy="46%" innerRadius={38} outerRadius={58} paddingAngle={2} isAnimationActive={false}>
                    {clusterPieData.map((_, i) => <Cell key={i} fill={DONUT_COLORS[i % DONUT_COLORS.length]} />)}
                  </Pie>
                  <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: 9.5, color: "#3C4864" }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div style={{ width: "100%", height: 190 }}>
              <ResponsiveContainer width="100%" height="100%" minWidth={100} debounce={50}>
                <PieChart>
                  <Tooltip contentStyle={chartTooltipStyle} itemStyle={{ color: "#D6E0F0" }} />
                  <Pie data={statusPieData} dataKey="value" nameKey="name" cx="50%" cy="46%" innerRadius={38} outerRadius={58} paddingAngle={2} isAnimationActive={false}>
                    <Cell fill="#0D9488" />
                    <Cell fill="#C4293E" />
                  </Pie>
                  <Legend verticalAlign="bottom" height={36} wrapperStyle={{ fontSize: 9.5, color: "#3C4864" }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        </ChartCard>
      </section>

      <section
        className="rounded-xl border p-5 mb-4"
        style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}
      >
        <div className="mb-4">
          <h2 className="text-[13.5px] font-bold" style={{ color: "var(--ink)" }}>Financial Performance × Quality</h2>
          <p className="text-[11.5px] mt-0.5 font-medium" style={{ color: "var(--slate-light)" }}>
            Each point is an ACO. Position shows expenditure gap vs. quality score; color flags ML-detected anomaly confidence.
          </p>
        </div>
        <div style={{ width: "100%", height: 400, minWidth: 300 }}>
        <ResponsiveContainer width="100%" height="100%" minWidth={300} debounce={50}>
          <ScatterChart margin={{ top: 10, right: 20, bottom: 10, left: 0 }}>
            <CartesianGrid stroke="#EEF1F7" />
            <XAxis
              type="number"
              dataKey="financial_pct"
              name="Expenditure Gap %"
              unit="%"
              tick={{ fontSize: 10.5, fontFamily: "Inter", fill: "#8993AC" }}
              axisLine={{ stroke: "#EEF1F7" }}
              tickLine={false}
              label={{ value: "Expenditure Gap (%)", position: "insideBottom", offset: -5, fontSize: 11, fill: "#8993AC" }}
            />
            <YAxis
              type="number"
              dataKey="quality"
              name="Quality Score"
              tick={{ fontSize: 10.5, fontFamily: "Inter", fill: "#8993AC" }}
              axisLine={{ stroke: "#EEF1F7" }}
              tickLine={false}
              label={{ value: "Quality Score", angle: -90, position: "insideLeft", fontSize: 11, fill: "#8993AC" }}
            />
            <ZAxis range={[40, 40]} />
            <Tooltip
              cursor={{ strokeDasharray: "3 3" }}
              content={({ active, payload }) => {
                if (!active || !payload?.length) return null;
                const p = payload[0].payload;
                return (
                  <div className="rounded-lg p-2.5 text-xs font-mono" style={{ background: "#101B33", color: "#D6E0F0" }}>
                    <div className="font-semibold text-white mb-0.5">{p.name}</div>
                    <div>Gap: {p.financial_pct.toFixed(1)}% · Quality: {p.quality.toFixed(1)}</div>
                    <div>Anomaly: {p.anomaly}</div>
                  </div>
                );
              }}
            />
            <Scatter data={financial_quality_bubbles} onClick={(d: any) => { window.location.href = `/acos/${d.aco_id}`; }}>
              {financial_quality_bubbles.map((d, i) => (
                <Cell key={i} fill={anomalyColor[d.anomaly] ?? "#A6AFC2"} fillOpacity={0.8} style={{ cursor: "pointer" }} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
        </div>
        <div className="flex gap-4 mt-2 text-[11px] font-medium" style={{ color: "var(--slate-light)" }}>
          <span><span className="inline-block w-2 h-2 rounded-full mr-1" style={{ background: "var(--loss)" }} />Very high confidence anomaly</span>
          <span><span className="inline-block w-2 h-2 rounded-full mr-1" style={{ background: "var(--anomaly)" }} />High confidence anomaly</span>
          <span><span className="inline-block w-2 h-2 rounded-full mr-1" style={{ background: "#A6AFC2" }} />Not flagged</span>
        </div>
      </section>

      <section
        className="rounded-xl border p-5"
        style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}
      >
        <h2 className="text-[13.5px] font-bold mb-1" style={{ color: "var(--ink)" }}>Top Opportunities</h2>
        <p className="text-[11px] mb-3 font-medium" style={{ color: "var(--slate-light)" }}>Ranked by combined driver score, ML anomaly confidence, and financial relevance.</p>

        <div className="overflow-x-auto">
          <table className="w-full text-sm" style={{ minWidth: 640 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)" }}>
                <th className="text-left pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>#</th>
                <th className="text-left pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>ACO</th>
                <th className="text-left pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Driver</th>
                <th className="text-right pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Priority</th>
                <th className="text-left pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Status</th>
                <th className="text-left pb-2.5 text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {top_opportunities.map((o) => (
                <tr key={o.priority_rank} style={{ borderBottom: "1px solid var(--border-soft)" }}>
                  <td className="py-3 text-[12.5px] font-mono" style={{ color: "var(--ink)" }}>{o.priority_rank}</td>
                  <td className="py-3 text-[12.5px] font-bold">
                    <Link to={`/acos/${o.ACO_ID}`} className="hover:underline" style={{ color: "var(--ink)" }}>
                      {o.ACO_Name}
                    </Link>
                  </td>
                  <td className="py-3 text-[12.5px] font-medium" style={{ color: "var(--slate)" }}>{o.driver_name}</td>
                  <td className="py-3 text-[12.5px] font-mono font-bold text-right" style={{ color: "var(--ink)" }}>{o.opportunity_priority.toFixed(1)}</td>
                  <td className="py-3">
                    <span
                      className="inline-flex px-2.5 py-1 rounded-full text-[10.5px] font-bold uppercase"
                      style={{
                        background: o.financial_status === "LOSS" ? "var(--loss-bg)" : "var(--savings-bg)",
                        color: o.financial_status === "LOSS" ? "var(--loss)" : "var(--savings)",
                      }}
                    >
                      {o.financial_status}
                    </span>
                  </td>
                  <td className="py-3 text-[12.5px] font-semibold" style={{ color: "var(--slate)" }}>{o.confidence}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
