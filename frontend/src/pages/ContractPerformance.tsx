import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  BarChart, Bar, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { api, type ContractsResponse } from "../services/api";
import KPICard from "../components/KPICard";

const tipStyle = { background: "#101B33", color: "#D6E0F0" };

function rollingAvg<T extends Record<string, any>>(rows: T[], keys: (keyof T)[], window: number): T[] {
  return rows.map((row, i) => {
    const start = Math.max(0, i - window + 1);
    const slice = rows.slice(start, i + 1);
    const smoothed: Record<string, any> = { ...row };
    for (const k of keys) {
      smoothed[k as string] = slice.reduce((sum, r) => sum + (r[k] as number), 0) / slice.length;
    }
    return smoothed as T;
  });
}

function fmtM(v: number) {
  const abs = Math.abs(v);
  if (abs >= 1e9) return `${v < 0 ? "-" : ""}$${(abs / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${v < 0 ? "-" : ""}$${(abs / 1e6).toFixed(1)}M`;
  return `${v < 0 ? "-" : ""}$${(abs / 1e3).toFixed(0)}K`;
}

export default function ContractPerformance() {
  const [data, setData] = useState<ContractsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedId, setSelectedId] = useState<string>("");

  useEffect(() => {
    api.contracts().then((d) => {
      setData(d);
      setSelectedId(d.contracts[0]?.aco_id ?? "");
    }).catch((e) => setError(String(e)));
  }, []);

  if (error) return <div className="p-8 font-mono text-sm" style={{ color: "var(--loss)" }}>Could not load contract data: {error}</div>;
  if (!data) return <div className="p-8" style={{ color: "var(--slate)" }}>Loading contract performance...</div>;

  const selected = data.contracts.find((c) => c.aco_id === selectedId) ?? data.contracts[0];

  const overviewRaw = [...data.contracts]
    .sort((a, b) => b.contract_health_score - a.contract_health_score)
    .map((c, i) => ({
      rank: i + 1,
      fullName: c.aco_name,
      Benchmark: c.benchmark,
      Expenditure: c.actual_expenditure,
      "Gross S/L": c.gross_savings_loss,
      Quality: c.quality_score,
      Risk: c.ml_risk_score,
    }));
  const overviewData = rollingAvg(overviewRaw, ["Benchmark", "Expenditure", "Gross S/L", "Quality", "Risk"], 20);

  return (
    <div className="max-w-7xl mx-auto px-7 py-8">
      <Link to="/" className="text-[12.5px] font-semibold" style={{ color: "var(--slate-light)" }}>← Command Center</Link>
      <h1 className="font-display text-[19px] mt-3 mb-1.5" style={{ color: "var(--ink)" }}>Contract Performance</h1>
      <p className="text-[12.5px] mb-5 font-medium" style={{ color: "var(--slate-light)" }}>
        Benchmark, settlement, and quality across all {data.total_contracts} MSSP contracts — Performance Year 2024.
      </p>

      <section className="grid grid-cols-2 lg:grid-cols-5 gap-3.5 mb-5">
        <KPICard label="Avg Contract Health" value={data.portfolio_avg_contract_health.toFixed(1)} sublabel="Portfolio average score, 0–100" />
        <KPICard label="Avg Quality" value={data.portfolio_avg_quality.toFixed(1)} sublabel="Portfolio average quality score" />
        <KPICard label="Avg Utilization" value={data.portfolio_avg_utilization.toFixed(1)} sublabel="Portfolio average utilization subscore" />
        <KPICard label="Total Benchmark" value={fmtM(data.portfolio_total_benchmark)} sublabel="Sum of CMS expenditure benchmarks" />
        <KPICard
          label="Total Gross Savings/Loss"
          value={fmtM(data.portfolio_total_gross_savings_loss)}
          sublabel={`Earned (after share/loss rate): ${fmtM(data.portfolio_total_earned_savings_loss)}`}
          tone={data.portfolio_total_gross_savings_loss >= 0 ? "savings" : "loss"}
        />
      </section>

      <section className="rounded-xl border p-5 mb-4" style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}>
        <div className="flex items-start justify-between flex-wrap gap-2 mb-1">
          <div>
            <h2 className="text-[13px] font-bold" style={{ color: "var(--ink)" }}>Portfolio Overview</h2>
            <p className="text-[11px] mt-0.5 font-medium" style={{ color: "var(--slate-light)" }}>
              All {data.total_contracts} contracts, ranked by Contract Health Score (descending) and shown as a 20-contract
              rolling average — left axis in $, right axis 0–100.
            </p>
          </div>
          <div className="flex flex-wrap gap-x-3 gap-y-1 text-[10.5px] font-semibold shrink-0">
            <span className="flex items-center gap-1" style={{ color: "#8993AC" }}><span className="inline-block w-2.5 h-[3px] rounded-full" style={{ background: "#A6AFC2" }} />Benchmark</span>
            <span className="flex items-center gap-1" style={{ color: "#8993AC" }}><span className="inline-block w-2.5 h-[3px] rounded-full" style={{ background: "#2461EA" }} />Expenditure</span>
            <span className="flex items-center gap-1" style={{ color: "#8993AC" }}><span className="inline-block w-2.5 h-[3px] rounded-full" style={{ background: "#0D9488" }} />Gross S/L</span>
            <span className="flex items-center gap-1" style={{ color: "#8993AC" }}><span className="inline-block w-2.5 h-[3px] rounded-full" style={{ background: "#B4720A" }} />Quality</span>
            <span className="flex items-center gap-1" style={{ color: "#8993AC" }}><span className="inline-block w-2.5 h-[3px] rounded-full" style={{ background: "#C4293E" }} />Risk</span>
          </div>
        </div>
        <div style={{ width: "100%", height: 340 }} className="mt-3">
          <ResponsiveContainer width="100%" height="100%" minWidth={300} debounce={50}>
            <AreaChart data={overviewData} margin={{ top: 5, right: 20, bottom: 5, left: 5 }}>
              <defs>
                {[
                  ["fillBenchmark", "#A6AFC2"],
                  ["fillExpenditure", "#2461EA"],
                  ["fillGross", "#0D9488"],
                  ["fillQuality", "#B4720A"],
                  ["fillRisk", "#C4293E"],
                ].map(([id, color]) => (
                  <linearGradient key={id} id={id} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={color} stopOpacity={0.32} />
                    <stop offset="100%" stopColor={color} stopOpacity={0} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid stroke="#EEF1F7" vertical={false} />
              <XAxis dataKey="rank" tick={{ fontSize: 10, fill: "#8993AC" }} axisLine={{ stroke: "#EEF1F7" }} tickLine={false}
                tickMargin={8} tickCount={10} />
              <YAxis yAxisId="left" tick={{ fontSize: 10, fill: "#8993AC" }} axisLine={{ stroke: "#EEF1F7" }} tickLine={false} tickFormatter={(v) => fmtM(v)} width={55} />
              <YAxis yAxisId="right" orientation="right" domain={[0, 100]} tick={{ fontSize: 10, fill: "#8993AC" }} axisLine={{ stroke: "#EEF1F7" }} tickLine={false} width={32} />
              <Tooltip
                contentStyle={tipStyle}
                itemStyle={{ color: "#D6E0F0" }}
                labelStyle={{ color: "#fff", fontWeight: 600 }}
                formatter={(v: any, name: any) => [["Benchmark", "Expenditure", "Gross S/L"].includes(String(name)) ? fmtM(Number(v)) : Number(v).toFixed(1), name]}
                labelFormatter={(l, p) => `Rank #${l} — near ${p?.[0]?.payload?.fullName ?? "—"} (20-contract avg)`}
              />
              <Area yAxisId="left" type="monotone" dataKey="Benchmark" stroke="#A6AFC2" strokeWidth={2.5} fill="url(#fillBenchmark)" dot={false} isAnimationActive={false} />
              <Area yAxisId="left" type="monotone" dataKey="Expenditure" stroke="#2461EA" strokeWidth={2.5} fill="url(#fillExpenditure)" dot={false} isAnimationActive={false} />
              <Area yAxisId="left" type="monotone" dataKey="Gross S/L" stroke="#0D9488" strokeWidth={2.5} fill="url(#fillGross)" dot={false} isAnimationActive={false} />
              <Area yAxisId="right" type="monotone" dataKey="Quality" stroke="#B4720A" strokeWidth={2.5} fill="url(#fillQuality)" dot={false} isAnimationActive={false} />
              <Area yAxisId="right" type="monotone" dataKey="Risk" stroke="#C4293E" strokeWidth={2.5} fill="url(#fillRisk)" dot={false} isAnimationActive={false} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </section>

      <section className="rounded-xl border p-5 mb-4" style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}>
        <div className="flex items-center justify-between mb-1 flex-wrap gap-2">
          <div>
            <h2 className="text-[13px] font-bold" style={{ color: "var(--ink)" }}>Gross → Earned Settlement</h2>
            <p className="text-[11px] mt-0.5 font-medium" style={{ color: "var(--slate-light)" }}>
              MSSP's real settlement step: Gross Savings/Loss × Final Share/Loss Rate = Earned Savings/Loss.
            </p>
          </div>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            className="text-[12px] font-semibold rounded-lg px-2.5 py-1.5 outline-none"
            style={{ border: "1px solid var(--border)", background: "var(--surface-2)", color: "var(--slate)" }}
          >
            {data.contracts.map((c) => <option key={c.aco_id} value={c.aco_id}>{c.aco_name}</option>)}
          </select>
        </div>
        {selected && (
          <div className="grid md:grid-cols-[1fr_auto_1fr] gap-4 items-center mt-4">
            <div style={{ width: "100%", height: 180 }}>
              <ResponsiveContainer width="100%" height="100%" minWidth={200} debounce={50}>
                <BarChart data={[{ name: "Gross", value: selected.gross_savings_loss }, { name: "Earned", value: selected.earned_savings_loss }]} margin={{ top: 5, right: 15, bottom: 5, left: 15 }}>
                  <CartesianGrid stroke="#EEF1F7" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 11, fill: "#3C4864", fontWeight: 600 }} axisLine={{ stroke: "#EEF1F7" }} tickLine={false} />
                  <YAxis tick={{ fontSize: 10, fill: "#8993AC" }} axisLine={{ stroke: "#EEF1F7" }} tickLine={false} tickFormatter={(v) => fmtM(v)} width={55} />
                  <Tooltip contentStyle={tipStyle} itemStyle={{ color: "#D6E0F0" }} formatter={(v: any) => [fmtM(Number(v)), ""]} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={70} isAnimationActive={false}>
                    <Cell fill={selected.financial_status === "LOSS" ? "#C4293E" : "#0D9488"} fillOpacity={0.55} />
                    <Cell fill={selected.financial_status === "LOSS" ? "#C4293E" : "#0D9488"} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
            <div className="text-center px-3">
              <div className="text-[10px] font-bold uppercase tracking-wide mb-1" style={{ color: "var(--slate-light)" }}>
                {selected.financial_status === "LOSS" ? "Final Loss Rate" : "Final Share Rate"}
              </div>
              <div className="font-mono text-[26px] font-bold" style={{ color: selected.financial_status === "LOSS" ? "var(--loss)" : "var(--savings)" }}>
                × {(selected.financial_status === "LOSS" ? selected.loss_rate : selected.share_rate).toFixed(1)}%
              </div>
            </div>
            <div className="text-[12.5px] leading-relaxed" style={{ color: "var(--slate)" }}>
              <strong style={{ color: "var(--ink)" }}>{selected.aco_name}</strong> recorded a gross{" "}
              <strong style={{ color: selected.financial_status === "LOSS" ? "var(--loss)" : "var(--savings)" }}>{selected.financial_status.toLowerCase()}</strong>{" "}
              of {fmtM(Math.abs(selected.gross_savings_loss))} against a ${(selected.benchmark / 1e6).toFixed(1)}M benchmark. After applying its{" "}
              {selected.financial_status === "LOSS" ? "final loss rate" : "final share rate"} of{" "}
              {(selected.financial_status === "LOSS" ? selected.loss_rate : selected.share_rate).toFixed(1)}%, the earned {selected.financial_status === "LOSS" ? "loss owed" : "shared savings"} is{" "}
              <strong style={{ color: "var(--ink)" }}>{fmtM(Math.abs(selected.earned_savings_loss))}</strong>.
              <Link to={`/acos/${selected.aco_id}`} className="block mt-2 font-bold hover:underline" style={{ color: "var(--accent)" }}>View full ACO detail →</Link>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
