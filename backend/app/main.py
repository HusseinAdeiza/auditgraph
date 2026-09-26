"""AuditGraph API — FastAPI app."""
from __future__ import annotations

import os

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import algorithms
from .cypher_templates import BY_ID, TEMPLATES
from .db import get_graph, graph_is_empty, query
from .etherscan import ingest_contract
from .pdf_report import export_report
from .seed import seed

app = FastAPI(title="AuditGraph API", version="1.0.0",
              description="Smart-contract vulnerability knowledge graph (FalkorDB + Cypher).")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

REPORT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "reports")
os.makedirs(REPORT_DIR, exist_ok=True)


@app.on_event("startup")
def _startup() -> None:
    if graph_is_empty():
        seed(force=False)


def _rows(res) -> tuple[list[str], list[list]]:
    """Normalize a FalkorDB result into (columns, rows). header = [[type, name], ...]."""
    cols = [h[1] for h in (res.header or [])]
    return cols, [list(r) for r in res.result_set]


@app.get("/api/health")
def health():
    try:
        res = query("MATCH (n) RETURN count(n) AS c")
        nodes = res.result_set[0][0]
    except Exception as e:  # noqa: BLE001
        return {"status": "falkordb_unreachable", "error": str(e)}
    return {"status": "ok", "graph": "audit", "nodes": int(nodes)}


@app.get("/api/templates")
def templates():
    return {"templates": [
        {"id": t["id"], "name": t["name"], "description": t["description"],
         "params": list(t["params"].keys())}
        for t in TEMPLATES
    ]}


@app.post("/api/query")
def run_query(body: dict):
    name = body.get("name")
    if name not in BY_ID:
        raise HTTPException(404, f"unknown template {name!r}; available: {sorted(BY_ID)}")
    t = BY_ID[name]
    params = body.get("params") or {}
    # apply defaults for optional params the frontend may omit
    if name == "contracts_with_vulnerability" and not params.get("swc"):
        cypher = t["cypher"].replace("WHERE v.swc = $swc", "WHERE 1=1")
    else:
        cypher = t["cypher"]
    try:
        res = query(cypher, params)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"query error: {e}")
    cols, rows = _rows(res)
    return {"name": name, "title": t["name"], "columns": cols, "rows": rows,
            "count": len(rows), "cypher": t["cypher"]}


@app.get("/api/contracts")
def contracts():
    res = query("MATCH (c:Contract) RETURN c.name AS name, c.chain AS chain, c.kind AS kind, c.protocol AS protocol "
                "ORDER BY c.name")
    cols = [h[1] for h in (res.header or [])]
    return {"contracts": [dict(zip(cols, r)) for r in res.result_set]}


@app.get("/api/graph/full")
def full_graph(limit: int = 400):
    """Whole graph (nodes+edges) for the Cytoscape view, capped for sanity."""
    nodes = []
    res = query("MATCH (n) RETURN id(n) AS id, labels(n) AS labels, properties(n) AS props LIMIT " + str(limit))
    for r in res.result_set:
        _, labels, props = r
        nodes.append({"data": {"id": f"n{len(nodes)}", "falkor_id": int(r[0]),
                               "label": labels[0], **props}})
    edges = []
    res2 = query("MATCH (a)-[r]->(b) RETURN id(a) AS a, id(b) AS b, type(r) AS t LIMIT " + str(limit * 4))
    id_map = {n["data"]["falkor_id"]: n["data"]["id"] for n in nodes}
    for r in res2.result_set:
        if r[0] in id_map and r[1] in id_map:
            edges.append({"data": {"id": f"e{len(edges)}", "source": id_map[r[0]],
                                   "target": id_map[r[1]], "type": r[2]}})
    return {"nodes": nodes, "edges": edges}


@app.get("/api/graph/neighborhood")
def neighborhood(name: str, depth: int = 2):
    """BFS from a node by name, for focused views."""
    depth = max(1, min(depth, 4))
    res = query(
        "MATCH (n {name: $name}) OPTIONAL MATCH (n)-[*1..{d}]-(m) RETURN id(n) AS nid, id(m) AS mid".replace(
            "{d}", str(depth)
        ),
        {"name": name},
    )
    ids: set[int] = set()
    for r in res.result_set:
        if r[0] is not None:
            ids.add(r[0])
        if r[1] is not None:
            ids.add(r[1])
    nodes: dict[int, dict] = {}
    for fid in ids:
        p = query("MATCH (x) WHERE id(x) = $fid RETURN labels(x) AS l, properties(x) AS p", {"fid": fid})
        if p.result_set:
            labels, props = p.result_set[0]
            nodes[fid] = {"data": {"id": f"n{len(nodes)}", "label": labels[0], **props}}
    id_map = {fid: n["data"]["id"] for fid, n in nodes.items()}
    edge_rows = query(
        "MATCH (a)-[r]->(b) WHERE id(a) IN $ids AND id(b) IN $ids "
        "RETURN id(a) AS a, id(b) AS b, type(r) AS t",
        {"ids": list(ids)},
    )
    out_edges = [{"data": {"id": f"e{i}", "source": id_map[r[0]], "target": id_map[r[1]], "type": r[2]}}
                 for i, r in enumerate(edge_rows.result_set)
                 if r[0] in id_map and r[1] in id_map]
    return {"nodes": list(nodes.values()), "edges": out_edges}


@app.post("/api/algorithms/{algo}")
def run_algorithm(algo: str, body: dict | None = None):
    params = (body or {}).get("params") or {}
    label = params.get("label")
    if algo == "pagerank":
        return algorithms.pagerank(top=int(params.get("top", 15)), label=label)
    if algo == "betweenness":
        return algorithms.betweenness(top=int(params.get("top", 15)), label=label)
    if algo == "shortest_path":
        if not params.get("source") or not params.get("target"):
            raise HTTPException(400, "shortest_path needs params.source and params.target")
        return algorithms.shortest_attack_path(params["source"], params["target"])
    if algo == "wcc":
        return algorithms.weakly_connected_components()
    if algo == "label_propagation":
        return algorithms.label_propagation()
    raise HTTPException(404, f"unknown algorithm {algo!r}")


@app.post("/api/ingest/etherscan")
def ingest(body: dict):
    from fastapi import HTTPException  # noqa: F401
    address = body.get("address", "").strip()
    if not (address.startswith("0x") and len(address) == 42):
        raise HTTPException(400, "address must be 0x-prefixed 42 hex chars")
    key = os.getenv("ETHERSCAN_API_KEY", "")
    try:
        return ingest_contract(address, body.get("name"), int(body.get("chain_id", 1)), key)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(502, f"etherscan ingest failed: {e}")


@app.post("/api/ingest/slither")
def slither_ingest(body: dict):
    from .slither import link_findings, run_slither

    src = body.get("source_path", "").strip()
    if not src or not os.path.exists(src):
        raise HTTPException(400, "source_path does not exist on this host")
    name = body.get("name") or os.path.basename(os.path.dirname(os.path.abspath(src)))
    res = run_slither(src, name)
    if res.get("status") != "ok":
        raise HTTPException(502, res.get("message", "slither failed"))
    linked = link_findings(name, res["findings"])
    return {**res, "graph": linked}


@app.post("/api/report/pdf")
def report_pdf(body: dict):
    contract = body.get("contract") or "full graph"
    queries = []
    for q in body.get("queries") or []:
        name = q.get("name")
        if name not in BY_ID:
            raise HTTPException(400, f"unknown query {name!r}")
        params = q.get("params") or {}
        t = BY_ID[name]
        cypher = t["cypher"]
        if name == "contracts_with_vulnerability" and not params.get("swc"):
            cypher = cypher.replace("WHERE v.swc = $swc", "WHERE 1=1")
        res = query(cypher, params)
        cols, rows = _rows(res)
        queries.append({"name": t["name"], "description": t["description"],
                        "columns": cols, "rows": rows})
    algos = []
    for a in body.get("algorithms") or []:
        try:
            if a == "pagerank":
                algos.append(algorithms.pagerank(top=10))
            elif a == "betweenness":
                algos.append(algorithms.betweenness(top=10))
            elif a == "wcc":
                algos.append(algorithms.weakly_connected_components())
        except Exception:  # noqa: BLE001
            continue
    stamp = "audit" if contract == "full graph" else contract.split(":")[-1][:24].strip()
    out_path = os.path.join(REPORT_DIR, f"auditgraph_{stamp}.pdf")
    export_report(out_path, f"AuditGraph report — {contract}", contract, queries, algos or None)
    return FileResponse(out_path, media_type="application/pdf",
                        filename=os.path.basename(out_path))


@app.post("/api/admin/reset")
def reset(x_admin_token: str = Header("")):
    # Destructive: wipes and re-seeds the graph. Requires AUDITGRAPH_ADMIN_TOKEN
    # to be set AND match, so a public demo can't be reset by a stray call.
    expected = os.getenv("AUDITGRAPH_ADMIN_TOKEN", "")
    if not expected or x_admin_token != expected:
        raise HTTPException(403, "admin token required")
    res = seed(force=True)
    return res


# Serve the built frontend if it's there. The Docker image puts it one level
# up (/app/app/main.py -> /app/frontend/dist); local dev is two levels up.
_DIST = os.environ.get("AUDITGRAPH_DIST") or next(
    (d for d in (
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend", "dist"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "frontend", "dist"),
    ) if os.path.isdir(d)), None)
if _DIST:
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="frontend")
