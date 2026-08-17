interface ScoreBreakdownProps {
  title: string;
  score: number;
  disclosure: string;
  components: { label: string; value: number; weight?: number }[];
}

export default function ScoreBreakdownCard({ title, score, disclosure, components }: ScoreBreakdownProps) {
  const scoreColor = score >= 70 ? "var(--savings)" : score >= 45 ? "var(--anomaly)" : "var(--loss)";
  return (
    <div className="rounded-xl border p-5" style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}>
      <div className="flex items-baseline justify-between mb-4">
        <h3 className="font-display text-[13.5px]" style={{ color: "var(--ink)" }}>{title}</h3>
        <span className="font-mono text-3xl font-bold" style={{ color: scoreColor }}>
          {score.toFixed(1)}
        </span>
      </div>
      <div className="mb-3">
        {components.map((c) => (
          <div key={c.label} className="grid items-center gap-3 mb-3.5 last:mb-0" style={{ gridTemplateColumns: "130px 1fr 44px" }}>
            <span className="text-[12.5px] font-semibold" style={{ color: "var(--slate)" }}>
              {c.label}{c.weight ? ` (${(c.weight * 100).toFixed(0)}%)` : ""}
            </span>
            <div className="h-[9px] rounded-[5px] overflow-hidden" style={{ background: "var(--surface-2)", border: "1px solid var(--border-soft)" }}>
              <div
                className="h-full rounded-[5px]"
                style={{ width: `${Math.min(c.value, 100)}%`, background: scoreColor }}
              />
            </div>
            <span className="font-mono text-[12.5px] font-bold text-right" style={{ color: "var(--ink)" }}>{c.value.toFixed(1)}</span>
          </div>
        ))}
      </div>
      <p className="text-[11px]" style={{ color: "var(--slate-light)" }}>
        {disclosure}
      </p>
    </div>
  );
}
