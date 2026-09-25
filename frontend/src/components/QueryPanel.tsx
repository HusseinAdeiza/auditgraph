import { useState } from "react";
import { runQuery, type QueryResult } from "../api";

function fmtCell(v: any): string {
  if (v === null || v === undefined) return "—";
  if (Array.isArray(v)) return `[${v.map(fmtCell).join(", ")}]`;
  if (typeof v === "number") return v > 999999 ? `$${(v / 1e6).toFixed(1)}M` : String(v);
  return String(v);
}

export default function QueryPanel({
  template, onResult,
}: {
  template: { id: string; name: string; description: string; params: string[] };
  onResult?: (r: QueryResult) => void;
}) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [result, setResult] = useState<QueryResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const run = async () => {
    setBusy(true); setError("");
    const params: Record<string, string> = {};
    for (const [k, v] of Object.entries(values)) if (v.trim()) params[k] = v.trim();
    try {
      const r = await runQuery(template.id, params);
      setResult(r); onResult?.(r);
    } catch (e: any) {
      setError(e.message || String(e));
    }
    setBusy(false);
  };

  return (
    <div className="space-y-3">
      <p className="text-sm text-slate-600">{template.description}</p>
      {template.params.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {template.params.map((p) => (
            <label key={p} className="text-xs text-slate-600">
              <span className="font-mono">{p}</span>
              <input
                value={values[p] || ""}
                onChange={(e) => setValues({ ...values, [p]: e.target.value })}
                className="ml-1 w-44 rounded border border-slate-300 px-2 py-1 text-xs font-mono focus:border-blue-500 focus:outline-none"
                placeholder={p}
              />
            </label>
          ))}
        </div>
      )}
      <button onClick={run} disabled={busy}
        className="rounded bg-blue-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-800 disabled:opacity-50">
        {busy ? "Running…" : "Run query"}
      </button>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {result && (
        <div className="max-h-80 overflow-auto scroll-thin rounded border border-slate-200">
          <table className="w-full text-left text-xs">
            <thead className="sticky top-0 bg-slate-100 text-slate-700">
              <tr>{result.columns.map((c) => <th key={c} className="px-2 py-1.5 font-semibold">{c}</th>)}</tr>
            </thead>
            <tbody>
              {result.rows.map((row, i) => (
                <tr key={i} className={i % 2 ? "bg-slate-50" : "bg-white"}>
                  {row.map((v, j) => <td key={j} className="px-2 py-1 text-slate-700">{fmtCell(v)}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
          <div className="border-t border-slate-200 bg-slate-50 px-2 py-1 text-xs text-slate-500">
            {result.count} rows · {result.title}
          </div>
        </div>
      )}
    </div>
  );
}
