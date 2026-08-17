import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from "recharts";

const CONFIDENCE_COLORS: Record<string, string> = { HIGH: "#C4293E", MEDIUM: "#B4720A", LOW: "#A6AFC2" };
const tipStyle = { background: "#101B33", color: "#D6E0F0" };

interface Opportunity {
  priority_rank: number;
  ACO_ID: string;
  ACO_Name: string;
  opportunity_priority: number;
  driver_name: string;
  evidence: string;
  ml_signal: string;
  financial_status: string;
  quality_band: string;
  confidence: string;
}

export default function Opportunities() {
  const [opps, setOpps] = useState<Opportunity[]>([]);
  const [filter, setFilter] = useState<"all" | "loss" | "high_confidence">("all");

  useEffect(() => {
    fetch("/api/opportunities?limit=100").then((r) => r.json()).then(setOpps);
  }, []);

  const filtered = opps.filter((o) => {
    if (filter === "loss") return o.financial_status === "LOSS";
    if (filter === "high_confidence") return o.confidence === "HIGH";
    return true;
  });

  return (
    <div className="max-w-6xl mx-auto px-7 py-8">
      <Link to="/" className="text-[12.5px] font-semibold" style={{ color: "var(--slate-light)" }}>← Command Center</Link>
      <h1 className="font-display text-[19px] mt-3 mb-1.5" style={{ color: "var(--ink)" }}>Review Opportunities</h1>
      <p className="text-[12.5px] mb-5 font-medium" style={{ color: "var(--slate-light)" }}>
        Ranked by combined driver score, ML anomaly confidence, and financial relevance.
      </p>

      <div className="flex gap-2 mb-5">
        {(["all", "loss", "high_confidence"] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className="px-3.5 py-1.5 rounded-full text-[11.5px] font-bold capitalize transition-colors"
            style={{
              background: filter === f ? "var(--accent)" : "var(--paper-raised)",
              color: filter === f ? "white" : "var(--slate)",
              border: filter === f ? "1px solid var(--accent)" : "1px solid var(--border)",
            }}
          >
            {f === "high_confidence" ? "High Confidence" : f}
          </button>
        ))}
      </div>

      <section className="grid lg:grid-cols-[1.4fr_1fr] gap-4 mb-4 items-stretch">
        <div className="rounded-xl border p-5" style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}>
          <h2 className="text-[13px] font-bold" style={{ color: "var(--ink)" }}>Priority Score — Top 15</h2>
          <p className="text-[11px] mt-0.5 mb-2 font-medium" style={{ color: "var(--slate-light)" }}>Within the current filter, highest priority first.</p>
          <div style={{ width: "100%", height: 340 }}>
            <ResponsiveContainer width="100%" height="100%" minWidth={280} debounce={50}>
              <BarChart
                data={filtered.slice(0, 15).map((o) => ({ name: o.ACO_Name.length > 24 ? o.ACO_Name.slice(0, 23) + "…" : o.ACO_Name, fullName: o.ACO_Name, priority: o.opportunity_priority, status: o.financial_status }))}
                layout="vertical" margin={{ top: 5, right: 25, bottom: 5, left: 5 }}
              >
                <CartesianGrid stroke="#EEF1F7" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: "#8993AC" }} axisLine={{ stroke: "#EEF1F7" }} tickLine={false} />
                <YAxis type="category" dataKey="name" width={175} tick={{ fontSize: 10, fill: "#3C4864" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={tipStyle} itemStyle={{ color: "#D6E0F0" }} labelStyle={{ color: "#fff", fontWeight: 600 }}
                  formatter={(v: any) => [Number(v).toFixed(1), "Priority score"]} labelFormatter={(_l, p) => p?.[0]?.payload?.fullName ?? ""} />
                <Bar dataKey="priority" radius={[0, 4, 4, 0]} maxBarSize={14} isAnimationActive={false}>
                  {filtered.slice(0, 15).map((o, i) => (
                    <Cell key={i} fill={o.financial_status === "LOSS" ? "#C4293E" : "#2461EA"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-xl border p-5" style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}>
          <h2 className="text-[13px] font-bold" style={{ color: "var(--ink)" }}>Confidence Mix</h2>
          <p className="text-[11px] mt-0.5 mb-2 font-medium" style={{ color: "var(--slate-light)" }}>{filtered.length} opportunities in current filter.</p>
          <div style={{ width: "100%", height: 300 }}>
            <ResponsiveContainer width="100%" height="100%" minWidth={200} debounce={50}>
              <PieChart>
                <Tooltip contentStyle={tipStyle} itemStyle={{ color: "#D6E0F0" }} />
                <Pie
                  data={["HIGH", "MEDIUM", "LOW"].map((c) => ({ name: c, value: filtered.filter((o) => o.confidence === c).length }))}
                  dataKey="value" nameKey="name" cx="50%" cy="46%" innerRadius={46} outerRadius={70} paddingAngle={2} isAnimationActive={false}
                >
                  {["HIGH", "MEDIUM", "LOW"].map((c) => <Cell key={c} fill={CONFIDENCE_COLORS[c]} />)}
                </Pie>
                <Legend verticalAlign="bottom" height={40} wrapperStyle={{ fontSize: 10, color: "#3C4864" }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section
        className="rounded-xl border overflow-hidden"
        style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}
      >
        <div className="overflow-x-auto">
          <table className="w-full text-sm" style={{ minWidth: 860 }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border)", background: "var(--surface-2)" }}>
                <th className="p-3 text-left text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>#</th>
                <th className="p-3 text-left text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>ACO</th>
                <th className="p-3 text-right text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Priority</th>
                <th className="p-3 text-left text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Driver</th>
                <th className="p-3 text-left text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Evidence</th>
                <th className="p-3 text-left text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>ML Signal</th>
                <th className="p-3 text-left text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Status</th>
                <th className="p-3 text-left text-[10px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((o) => (
                <tr key={o.priority_rank} className="text-xs" style={{ borderBottom: "1px solid var(--border-soft)" }}>
                  <td className="p-3 font-mono" style={{ color: "var(--ink)" }}>{o.priority_rank}</td>
                  <td className="p-3">
                    <Link to={`/acos/${o.ACO_ID}`} className="hover:underline font-bold" style={{ color: "var(--ink)" }}>
                      {o.ACO_Name}
                    </Link>
                  </td>
                  <td className="p-3 font-mono font-bold text-right" style={{ color: "var(--ink)" }}>{o.opportunity_priority.toFixed(1)}</td>
                  <td className="p-3 font-medium" style={{ color: "var(--slate)" }}>{o.driver_name}</td>
                  <td className="p-3 font-mono" style={{ color: "var(--slate-light)" }}>{o.evidence}</td>
                  <td className="p-3 font-medium" style={{ color: "var(--slate-light)" }}>{o.ml_signal}</td>
                  <td className="p-3">
                    <span
                      className="inline-flex px-2.5 py-1 rounded-full text-[10px] font-bold uppercase"
                      style={{
                        background: o.financial_status === "LOSS" ? "var(--loss-bg)" : "var(--savings-bg)",
                        color: o.financial_status === "LOSS" ? "var(--loss)" : "var(--savings)",
                      }}
                    >
                      {o.financial_status}
                    </span>
                  </td>
                  <td className="p-3 font-semibold" style={{ color: "var(--slate)" }}>{o.confidence}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
