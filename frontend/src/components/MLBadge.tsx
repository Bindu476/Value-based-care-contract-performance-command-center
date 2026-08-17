export default function MLBadge({ children }: { children: React.ReactNode }) {
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[10.5px] font-bold uppercase tracking-wide"
      style={{ background: "var(--anomaly-bg)", color: "var(--anomaly)" }}
      title="Application interpretation from ML analysis — not an official CMS classification"
    >
      <svg width="8" height="8" viewBox="0 0 8 8" fill="currentColor"><circle cx="4" cy="4" r="4" /></svg>
      ML-Detected · {children}
    </span>
  );
}
