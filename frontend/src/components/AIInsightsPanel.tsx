import { useState } from "react";
import { api, type AskResponse } from "../services/api";

const HISTORY_LIMIT = 5;

export default function AIInsightsPanel({ acoId }: { acoId: string }) {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [current, setCurrent] = useState<AskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<AskResponse[]>([]);

  const submit = () => {
    const q = question.trim();
    if (!q || loading) return;
    setLoading(true);
    setError(null);
    api
      .askAboutAco(acoId, q)
      .then((res) => {
        setCurrent(res);
        setHistory((h) => [res, ...h].slice(0, HISTORY_LIMIT));
        setQuestion("");
      })
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  };

  return (
    <div
      className="rounded-xl border p-5"
      style={{ borderColor: "var(--border)", background: "var(--paper-raised)", boxShadow: "var(--glass-shadow)" }}
    >
      <h3 className="text-[13.5px] font-bold mb-3.5" style={{ color: "var(--ink)" }}>AI Insights</h3>
      <p className="text-xs mb-3" style={{ color: "var(--slate)" }}>
        Ask a question about this ACO. Answers are grounded strictly in the evidence shown on this page.
      </p>

      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") submit();
          }}
          placeholder="e.g. Why is this ACO flagged as an anomaly?"
          maxLength={500}
          disabled={loading}
          className="flex-1 px-3 py-2 rounded-lg border text-[12.5px]"
          style={{ borderColor: "var(--border)", background: "var(--paper)", color: "var(--ink)" }}
        />
        <button
          onClick={submit}
          disabled={loading || !question.trim()}
          className="px-3.5 py-2 rounded-lg text-xs font-bold border disabled:opacity-50"
          style={{ borderColor: "var(--border)", color: "white", background: "var(--accent)" }}
        >
          {loading ? "Asking..." : "Ask"}
        </button>
      </div>

      {error && (
        <div className="text-xs p-3 rounded border mb-3" style={{ borderColor: "var(--loss)", color: "var(--loss)" }}>
          {error}
        </div>
      )}

      {current && (
        <div className="mb-4">
          <div className="text-xs font-semibold mb-1" style={{ color: "var(--slate)" }}>{current.question}</div>
          {current.status === "ok" ? (
            <p className="text-sm leading-relaxed">{current.answer}</p>
          ) : (
            <div
              className="text-xs p-3 rounded border"
              style={{ borderColor: "var(--anomaly)", background: "var(--anomaly-bg)", color: "var(--ink)" }}
            >
              <strong>Answer generation unavailable — showing structured data below.</strong>
              {current.reason && <div className="mt-1 font-mono">{current.reason}</div>}
            </div>
          )}
        </div>
      )}

      {history.length > 1 && (
        <div className="pt-3 border-t" style={{ borderColor: "var(--border)" }}>
          <div className="text-[10px] font-bold uppercase tracking-wide mb-2" style={{ color: "var(--slate-light)" }}>
            Previous Questions
          </div>
          <ul className="space-y-2.5">
            {history.slice(1).map((h, i) => (
              <li key={i}>
                <div className="text-xs font-semibold mb-0.5" style={{ color: "var(--slate)" }}>{h.question}</div>
                {h.status === "ok" ? (
                  <p className="text-xs leading-relaxed" style={{ color: "var(--slate)" }}>{h.answer}</p>
                ) : (
                  <p className="text-xs italic" style={{ color: "var(--slate-light)" }}>
                    Answer unavailable{h.reason ? ` — ${h.reason}` : ""}
                  </p>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
