export interface CyNode { data: { id: string; label?: string; [k: string]: any } }
export interface CyEdge { data: { id: string; source: string; target: string; type?: string } }
export interface GraphData { nodes: CyNode[]; edges: CyEdge[] }

export interface Template { id: string; name: string; description: string; params: string[] }

export interface QueryResult {
  name: string; title: string; columns: string[];
  rows: any[][]; count: number; cypher: string;
}

export async function getTemplates(): Promise<Template[]> {
  const r = await fetch("/api/templates"); return (await r.json()).templates;
}
export async function runQuery(name: string, params: Record<string, string | number>): Promise<QueryResult> {
  // FalkorDB needs LIMIT / variable-length params as numbers, not strings.
  const coerced: Record<string, string | number> = {};
  for (const [k, v] of Object.entries(params)) {
    if (typeof v === "string" && v.trim() !== "" && /^-?\d+(\.\d+)?$/.test(v.trim())) {
      coerced[k] = Number(v.trim());
    } else {
      coerced[k] = v;
    }
  }
  const r = await fetch("/api/query", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, params: coerced }),
  });
  if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
  return r.json();
}
export async function getContracts(): Promise<{ name: string; chain: string; kind: string; protocol: string }[]> {
  const r = await fetch("/api/contracts"); return (await r.json()).contracts;
}
export async function getFullGraph(limit = 500): Promise<GraphData> {
  const r = await fetch(`/api/graph/full?limit=${limit}`); return r.json();
}
export async function getNeighborhood(name: string, depth = 2): Promise<GraphData> {
  const r = await fetch(`/api/graph/neighborhood?name=${encodeURIComponent(name)}&depth=${depth}`);
  return r.json();
}
export async function runAlgo(algo: string, params: Record<string, any>): Promise<any> {
  const r = await fetch(`/api/algorithms/${algo}`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ params }),
  });
  if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
  return r.json();
}
export async function health(): Promise<any> {
  const r = await fetch("/api/health"); return r.json();
}
export function reportPdf(contract: string, queries: { name: string; params: Record<string, string> }[], algos: string[]): void {
  const blob = fetch("/api/report/pdf", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ contract, queries, algorithms: algos }),
  }).then((r) => r.blob()).then((b) => {
    const url = URL.createObjectURL(b);
    const a = document.createElement("a");
    a.href = url; a.download = `auditgraph_${contract.replace(/[^a-z0-9]/gi, "_")}.pdf`;
    a.click(); URL.revokeObjectURL(url);
  });
}
