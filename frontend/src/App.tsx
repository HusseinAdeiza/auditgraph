import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getContracts, getFullGraph, getNeighborhood, getTemplates, health,
  reportPdf, runAlgo, runQuery,
  type GraphData, type QueryResult, type Template,
} from "./api";
import GraphView, { GraphLegend } from "./components/GraphView";
import QueryPanel from "./components/QueryPanel";

type Tab = "graph" | "queries" | "algorithms" | "ingest" | "report";

const NODE_DETAIL_LABELS: Record<string, string[]> = {
  Contract: ["address", "chain", "kind", "protocol", "verified", "compiler"],
  Vulnerability: ["swc", "severity", "category", "description", "mitigation"],
  Exploit: ["name", "year", "loss_usd", "chain", "summary"],
  Function: ["name", "description"],
  Library: ["name", "version", "usage"],
  Auditor: ["name"],
};

export default function App() {
  const [tab, setTab] = useState<Tab>("graph");
  const [healthState, setHealthState] = useState<any>(null);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [contracts, setContracts] = useState<{ name: string }[]>([]);
  const [graph, setGraph] = useState<GraphData>({ nodes: [], edges: [] });
  const [focus, setFocus] = useState("");
  const [selected, setSelected] = useState<any>(null);
  const [reportQueries, setReportQueries] = useState<QueryResult[]>([]);
  const [reportContract, setReportContract] = useState("full graph");
  const [reportStatus, setReportStatus] = useState("");
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    health().then(setHealthState).catch(() => setHealthState({ status: "offline" }));
    getTemplates().then(setTemplates).catch(() => {});
    getContracts().then((c) => setContracts(c)).catch(() => {});
  }, []);

  const loadFull = useCallback(async () => {
    setBusy("graph"); setError("");
    try { setGraph(await getFullGraph(500)); setFocus(""); }
    catch (e: any) { setError(e.message); }
    setBusy("");
  }, []);
  useEffect(() => { if (tab === "graph") loadFull(); }, [tab, loadFull]);

  const onNodeSelect = useCallback((n: any) => {
    setSelected(n);
    if (n.label === "Contract") setFocus(n.id);
  }, []);

  const focusContract = async (name: string) => {
    setBusy("focus"); setError(""); setSelected(null);
    try {
      const g = await getNeighborhood(name, 2);
      setGraph(g); setFocus("");
    } catch (e: any) { setError(e.message); }
    setBusy("");
  };

  const detailFields = useMemo(() => {
    if (!selected) return [];
    const keys = NODE_DETAIL_LABELS[selected.label] || [];
    const out: [string, string][] = [["label", selected.label]];
    if (selected.name) out.push(["name", String(selected.name)]);
    for (const k of keys) if (selected[k] !== undefined && selected[k] !== null) out.push([k, String(selected[k])]);
    return out;
  }, [selected]);

  const detailTitle = selected?.name || selected?.swc || (selected ? selected.label : "");

  return (
    <div className="flex h-full flex-col">
      <header className="border-b border-slate-200 bg-white px-6 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded bg-blue-700 font-bold text-white">AG</div>
            <div>
              <h1 className="text-base font-semibold leading-tight text-slate-900">AuditGraph</h1>
              <p className="text-xs text-slate-500">Smart contract vulnerability knowledge graph · FalkorDB + Cypher</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 font-medium ${
              healthState?.status === "ok" ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>
              <span className={`h-2 w-2 rounded-full ${healthState?.status === "ok" ? "bg-emerald-500" : "bg-red-500"}`} />
              {healthState?.status === "ok" ? `graph: ${healthState.nodes} nodes` : "backend offline"}
            </span>
          </div>
        </div>
        <nav className="mt-3 flex gap-1">
          {([["graph", "Graph"], ["queries", "Queries"], ["algorithms", "Algorithms"], ["ingest", "Ingest"], ["report", "Report"]] as [Tab, string][]).map(([t, label]) => (
            <button key={t} onClick={() => setTab(t)}
              className={`rounded px-3 py-1.5 text-sm font-medium ${tab === t ? "bg-blue-700 text-white" : "text-slate-600 hover:bg-slate-100"}`}>
              {label}
            </button>
          ))}
        </nav>
      </header>

      {error && (
        <div className="border-b border-red-200 bg-red-50 px-6 py-2 text-sm text-red-700">{error}</div>
      )}

      <main className="flex-1 overflow-auto p-6">
        {tab === "graph" && (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
            <div className="flex flex-col gap-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <label className="text-xs text-slate-600">Focus contract</label>
                  <select
                    className="rounded border border-slate-300 bg-white px-2 py-1 text-sm"
                    value=""
                    onChange={(e) => e.target.value && focusContract(e.target.value)}>
                    <option value="">— full graph ({graph.nodes.length || "…"}) —</option>
                    {contracts.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
                  </select>
                  <button onClick={loadFull} disabled={busy === "graph"}
                    className="rounded border border-slate-300 bg-white px-2.5 py-1 text-sm hover:bg-slate-50 disabled:opacity-50">
                    {busy === "graph" ? "Loading…" : "Reset"}
                  </button>
                </div>
                <GraphLegend />
              </div>
              <div className="h-[calc(100vh-220px)] min-h-[480px]">
                <GraphView data={graph} onSelect={onNodeSelect} focus={focus} />
              </div>
              <p className="text-xs text-slate-500">
                Click any node for details · drag to pan · scroll to zoom · {graph.nodes.length} nodes, {graph.edges.length} edges
              </p>
            </div>
            <aside className="rounded-lg border border-slate-200 bg-white p-4">
              <h3 className="text-sm font-semibold text-slate-800">Node details</h3>
              {!selected && <p className="mt-2 text-sm text-slate-500">Select a node in the graph.</p>}
              {selected && (
                <div className="mt-2">
                  <div className="text-lg font-semibold text-slate-900">{detailTitle}</div>
                  <dl className="mt-3 space-y-2 text-sm">
                    {detailFields.map(([k, v]) => (
                      <div key={k}>
                        <dt className="text-xs uppercase tracking-wide text-slate-400">{k}</dt>
                        <dd className="break-words text-slate-700">{v}</dd>
                      </div>
                    ))}
                  </dl>
                  {selected.label === "Exploit" && selected.loss_usd > 0 && (
                    <div className="mt-3 rounded bg-amber-50 px-3 py-2 text-sm text-amber-800">
                      Loss: ${Number(selected.loss_usd).toLocaleString()}
                    </div>
                  )}
                </div>
              )}
            </aside>
          </div>
        )}

        {tab === "queries" && (
          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            {templates.map((t) => (
              <div key={t.id} className="rounded-lg border border-slate-200 bg-white p-4">
                <h3 className="text-sm font-semibold text-slate-800">{t.name}</h3>
                <p className="mb-3 font-mono text-xs text-slate-400">{t.id}</p>
                <QueryPanel
                  template={t}
                  onResult={(r) => {
                    setReportQueries((prev) => [...prev.filter((q) => q.name !== r.name), r]);
                    const contractRow = r.rows?.[0]?.[0];
                    if (r.name === "contracts_with_vulnerability" && contractRow) setReportContract(String(contractRow));
                  }}
                />
              </div>
            ))}
          </div>
        )}

        {tab === "algorithms" && <AlgorithmsTab />}
        {tab === "ingest" && <IngestTab />}

        {tab === "report" && (
          <div className="max-w-2xl rounded-lg border border-slate-200 bg-white p-6">
            <h3 className="text-base font-semibold text-slate-900">Export PDF audit report</h3>
            <p className="mt-1 text-sm text-slate-600">
              Bundles the queries you have run (with their live results) plus the selected graph algorithms into a
              formatted PDF.
            </p>
            <div className="mt-4">
              <label className="text-xs text-slate-600">Report subject</label>
              <input value={reportContract} onChange={(e) => setReportContract(e.target.value)}
                className="mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm" />
            </div>
            <div className="mt-4">
              <label className="text-xs text-slate-600">Queries included ({reportQueries.length})</label>
              <ul className="mt-1 space-y-1">
                {reportQueries.length === 0 && <li className="text-sm text-slate-400">None yet — run queries on the Queries tab.</li>}
                {reportQueries.map((q) => (
                  <li key={q.name} className="flex items-center justify-between rounded bg-slate-50 px-3 py-1.5 text-sm">
                    <span>{q.title}</span>
                    <span className="text-xs text-slate-500">{q.count} rows</span>
                  </li>
                ))}
              </ul>
            </div>
            <button
              onClick={() => {
                setReportStatus("generating…");
                const q = reportQueries.map((q) => ({ name: q.name, params: q.params || {} }));
                reportPdf(reportContract, q, ["pagerank"])
                  .then(() => setReportStatus("report downloaded — check your downloads folder"))
                  .catch(() => setReportStatus("report failed"));
              }}
              disabled={reportQueries.length === 0 || reportStatus === "generating…"}
              className="mt-5 rounded bg-blue-700 px-4 py-2 text-sm font-medium text-white hover:bg-blue-800 disabled:opacity-50">
              Generate & download PDF
            </button>
            {reportStatus && <p className="mt-2 text-sm text-slate-600">{reportStatus}</p>}
          </div>
        )}
      </main>
    </div>
  );
}

function AlgorithmsTab() {
  const [contracts, setContracts] = useState<{ name: string }[]>([]);
  const [src, setSrc] = useState(""); const [dst, setDst] = useState("");
  const [results, setResults] = useState<Record<string, any>>({});
  const [busy, setBusy] = useState(""); const [error, setError] = useState("");

  useEffect(() => { getContracts().then(setContracts).catch(() => {}); }, []);

  const run = async (algo: string, params: Record<string, any>) => {
    setBusy(algo); setError("");
    try {
      const d = await runAlgo(algo, params);
      setResults((r) => ({ ...r, [algo]: d }));
    } catch (e: any) { setError(e.message); }
    setBusy("");
  };

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h3 className="text-sm font-semibold text-slate-800">Centrality & communities</h3>
        <div className="mt-3 flex flex-wrap gap-2">
          <button onClick={() => run("pagerank", {})} disabled={busy === "pagerank"}
            className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50">PageRank top 15</button>
          <button onClick={() => run("betweenness", {})} disabled={busy === "betweenness"}
            className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50">Betweenness top 15</button>
          <button onClick={() => run("wcc", {})} disabled={busy === "wcc"}
            className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50">Weakly connected components</button>
          <button onClick={() => run("label_propagation", {})} disabled={busy === "label_propagation"}
            className="rounded border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50">Label propagation</button>
        </div>
      </div>
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h3 className="text-sm font-semibold text-slate-800">Shortest attack path</h3>
        <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
          <select value={src} onChange={(e) => setSrc(e.target.value)} className="rounded border border-slate-300 px-2 py-1.5">
            <option value="">source…</option>
            {contracts.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
          </select>
          <span className="text-slate-400">→</span>
          <select value={dst} onChange={(e) => setDst(e.target.value)} className="rounded border border-slate-300 px-2 py-1.5">
            <option value="">target…</option>
            {contracts.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
          </select>
          <button onClick={() => run("shortest_path", { source: src, target: dst })}
            disabled={!src || !dst || busy === "shortest_path"}
            className="rounded bg-blue-700 px-3 py-1.5 font-medium text-white hover:bg-blue-800 disabled:opacity-50">
            Find path
          </button>
        </div>
      </div>
      {error && <div className="lg:col-span-2 rounded bg-red-50 px-4 py-2 text-sm text-red-700">{error}</div>}
      {Object.entries(results).map(([algo, r]) => (
        <div key={algo} className="lg:col-span-2 rounded-lg border border-slate-200 bg-white p-4">
          <h4 className="text-sm font-semibold text-slate-800">{algo}</h4>
          {"nodes" in r && (
            <table className="mt-2 w-full text-left text-sm">
              <thead><tr className="text-xs uppercase text-slate-400"><th className="py-1">node</th><th>label</th><th>score</th></tr></thead>
              <tbody>
                {r.nodes.map((n: any, i: number) => (
                  <tr key={i} className="border-t border-slate-100"><td className="py-1 font-mono">{n.name}</td><td>{n.label}</td><td className="font-mono">{n.score}</td></tr>
                ))}
              </tbody>
            </table>
          )}
          {"path" in r && (
            <div className="mt-2 flex flex-wrap items-center gap-1 text-sm">
              {r.path.map((p: string, i: number) => (
                <span key={i} className="flex items-center gap-1">
                  <span className="rounded bg-blue-50 px-2 py-1 font-mono text-blue-800">{p}</span>
                  {i < r.path.length - 1 && <span className="text-slate-400">→</span>}
                </span>
              ))}
              <span className="ml-2 text-xs text-slate-500">{r.hops} hops</span>
            </div>
          )}
          {"components" in r && (
            <div className="mt-2 space-y-2">
              <p className="text-xs text-slate-500">{r.count} components · largest {r.largest ?? "n/a"}</p>
              {(r.components || []).slice(0, 6).map((c: any) => (
                <div key={c.id} className="rounded bg-slate-50 px-3 py-2 text-sm">
                  <span className="font-semibold">cluster {c.id}</span> <span className="text-slate-500">({c.size})</span>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {(c.members || []).slice(0, 12).map((m: string) => (
                      <span key={m} className="rounded bg-white px-1.5 py-0.5 font-mono text-xs text-slate-600">{m}</span>
                    ))}
                    {c.size > 12 && <span className="text-xs text-slate-400">+{c.size - 12}</span>}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function IngestTab() {
  const [address, setAddress] = useState("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D");
  const [slitherPath, setSlitherPath] = useState("");
  const [out, setOut] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(""); const [error, setError] = useState("");

  const doEtherscan = async () => {
    setBusy("eth"); setError("");
    try {
      const r = await fetch("/api/ingest/etherscan", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ address }),
      });
      const d = await r.json();
      setOut((o) => ({ ...o, etherscan: r.ok ? `✔ ${d.contract}: verified=${d.verified}, proxy=${d.is_proxy}, ${d.compiler}` : `✖ ${d.detail || JSON.stringify(d)}` }));
    } catch (e: any) { setError(e.message); }
    setBusy("");
  };
  const doSlither = async () => {
    setBusy("slither"); setError("");
    try {
      const r = await fetch("/api/ingest/slither", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_path: slitherPath }),
      });
      const d = await r.json();
      setOut((o) => ({ ...o, slither: r.ok ? `✔ ${d.findings?.length ?? 0} findings linked to graph` : `✖ ${d.detail || JSON.stringify(d)}` }));
    } catch (e: any) { setError(e.message); }
    setBusy("");
  };

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h3 className="text-sm font-semibold text-slate-800">Etherscan ingestion</h3>
        <p className="mt-1 text-xs text-slate-500">Pull a contract's verification/proxy status from Etherscan and add it to the graph.</p>
        <div className="mt-3 flex gap-2">
          <input value={address} onChange={(e) => setAddress(e.target.value)}
            className="flex-1 rounded border border-slate-300 px-2 py-1.5 font-mono text-sm" placeholder="0x…" />
          <button onClick={doEtherscan} disabled={busy === "eth"}
            className="rounded bg-blue-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-800 disabled:opacity-50">
            {busy === "eth" ? "…" : "Ingest"}
          </button>
        </div>
        {out.etherscan && <p className="mt-2 text-sm text-slate-700">{out.etherscan}</p>}
      </div>
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h3 className="text-sm font-semibold text-slate-800">Slither static analysis</h3>
        <p className="mt-1 text-xs text-slate-500">Run Slither over a local Solidity path; findings are mapped to SWC ids and linked to the graph. Requires <code className="rounded bg-slate-100 px-1">slither</code> in PATH.</p>
        <div className="mt-3 flex gap-2">
          <input value={slitherPath} onChange={(e) => setSlitherPath(e.target.value)}
            className="flex-1 rounded border border-slate-300 px-2 py-1.5 font-mono text-sm" placeholder="/path/to/contracts/" />
          <button onClick={doSlither} disabled={busy === "slither" || !slitherPath}
            className="rounded bg-blue-700 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-800 disabled:opacity-50">
            {busy === "slither" ? "…" : "Analyze"}
          </button>
        </div>
        {out.slither && <p className="mt-2 text-sm text-slate-700">{out.slither}</p>}
      </div>
      {error && <div className="lg:col-span-2 rounded bg-red-50 px-4 py-2 text-sm text-red-700">{error}</div>}
    </div>
  );
}
