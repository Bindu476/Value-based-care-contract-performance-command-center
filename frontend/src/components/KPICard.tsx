interface KPICardProps {
  label: string;
  value: string;
  sublabel?: string;
  tone?: "default" | "savings" | "loss" | "anomaly";
}

const toneColor = {
  default: "var(--ink)",
  savings: "var(--savings)",
  loss: "var(--loss)",
  anomaly: "var(--anomaly)",
};

export default function KPICard({ label, value, sublabel, tone = "default" }: KPICardProps) {
  const color = toneColor[tone];
  return (
    <div
      className="rounded-xl border p-4 flex flex-col gap-2.5"
      style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}
    >
      <div className="flex items-center gap-1.5">
        {tone !== "default" && <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: color }} />}
        <span className="text-[11px] font-bold uppercase tracking-wide" style={{ color: "var(--slate-light)" }}>
          {label}
        </span>
      </div>
      <span className="font-mono text-[25px] font-bold" style={{ color, letterSpacing: "-0.5px" }}>
        {value}
      </span>
      {sublabel && (
        <span className="text-xs font-medium" style={{ color: "var(--slate-light)" }}>
          {sublabel}
        </span>
      )}
    </div>
  );
}
