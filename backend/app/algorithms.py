"""Graph algorithms over the full graph, computed with networkx.

FalkorDB has built-in algos, but for a hackathon demo a transparent
networkx pass over the queried subgraph is more inspectable and easier to
explain in the writeup.
"""
from __future__ import annotations

import networkx as nx

from .db import query


def _load_full_graph() -> nx.DiGraph:
    g = nx.DiGraph()
    rows = query("MATCH (n) RETURN id(n) AS id, labels(n) AS labels, properties(n) AS props")
    for r in rows.result_set:
        node_id, labels, props = r
        g.add_node(int(node_id), label=labels[0], name=props.get("name", props.get("swc", "?")))
    rows = query("MATCH (a)-[r]->(b) RETURN id(a) AS a, id(b) AS b, type(r) AS t")
    for r in rows.result_set:
        g.add_edge(int(r[0]), int(r[1]), rel=r[2])
    return g


def _resolve(name: str, label: str) -> list[int]:
    res = query(f"MATCH (n:{label} {{name: $name}}) RETURN id(n) AS id", {"name": name})
    return [int(r[0]) for r in res.result_set]


def _pagerank_pure(g: nx.DiGraph, alpha: float = 0.85, max_iter: int = 100, tol: float = 1e-8) -> dict:
    """Pure-Python PageRank (avoids the numpy/scipy dependency)."""
    nodes = list(g.nodes())
    if not nodes:
        return {}
    out = {n: set() for n in nodes}
    for u, v in g.edges():
        out[u].add(v)
    rank = {n: 1.0 / len(nodes) for n in nodes}
    for _ in range(max_iter):
        dangling = sum(rank[n] for n in nodes if not out[n])
        new = {}
        for n in nodes:
            new[n] = (1 - alpha) / len(nodes)
        for u in nodes:
            if out[u]:
                share = alpha * rank[u] / len(out[u])
                for v in out[u]:
                    new[v] = new[v] + share
        new = {n: new[n] + alpha * dangling / len(nodes) for n in new}
        delta = sum(abs(new[n] - rank[n]) for n in nodes)
        rank = new
        if delta < tol:
            break
    return rank


def _label_propagation_pure(gu: nx.Graph) -> list[list]:
    """Pure-Python label propagation communities (deterministic seed)."""
    import random

    rng = random.Random(42)
    nodes = list(gu.nodes())
    if not nodes:
        return []
    label = {n: i for i, n in enumerate(nodes)}
    order = nodes[:]
    rng.shuffle(order)
    for _ in range(10):  # passes
        changed = False
        for n in order:
            neighbors = list(gu.neighbors(n))
            if not neighbors:
                continue
            tally: dict[int, int] = {}
            for nb in neighbors:
                tally[label[nb]] = tally.get(label[nb], 0) + 1
            best = max(tally.items(), key=lambda kv: (kv[1], -kv[0]))[0]
            if best != label[n]:
                label[n] = best
                changed = True
        if not changed:
            break
    groups: dict[int, list] = {}
    for n in nodes:
        groups.setdefault(label[n], []).append(n)
    return [g for _, g in sorted(groups.items(), key=lambda kv: -len(kv[1]))]


def _label_propagation(g: nx.DiGraph) -> list[list]:
    gu = g.to_undirected()
    try:
        from networkx.algorithms.community import label_propagation_communities

        return list(label_propagation_communities(gu))
    except Exception:  # noqa: BLE001
        return _label_propagation_pure(gu)


def pagerank(top: int = 15, label: str | None = None) -> dict:
    g = _load_full_graph()
    if label:
        g = g.subgraph(n for n, d in g.nodes(data=True) if d.get("label") == label)
    if not g.number_of_nodes():
        return {"nodes": [], "note": "empty graph"}
    try:
        pr = nx.pagerank(g, alpha=0.85)
    except Exception:  # noqa: BLE001  # numpy missing in some envs
        pr = _pagerank_pure(g)
    ranked = sorted(pr.items(), key=lambda kv: kv[1], reverse=True)[:top]
    out = []
    for nid, score in ranked:
        d = g.nodes[nid]
        out.append(dict(name=d.get("name"), label=d.get("label"), score=round(score, 5)))
    return {"algorithm": "pagerank", "nodes": out}


def betweenness(top: int = 15, label: str | None = None) -> dict:
    g = _load_full_graph()
    if label:
        g = g.subgraph(n for n, d in g.nodes(data=True) if d.get("label") == label)
    if not g.number_of_nodes():
        return {"nodes": [], "note": "empty graph"}
    bc = nx.betweenness_centrality(g, normalized=True)
    ranked = sorted(bc.items(), key=lambda kv: kv[1], reverse=True)[:top]
    out = []
    for nid, score in ranked:
        d = g.nodes[nid]
        out.append(dict(name=d.get("name"), label=d.get("label"), score=round(score, 5)))
    return {"algorithm": "betweenness_centrality", "nodes": out}


def shortest_attack_path(source: str, target: str) -> dict:
    g = _load_full_graph()
    sources = _resolve(source, "Contract") or _resolve(source, "Function")
    targets = _resolve(target, "Contract") or _resolve(target, "Function")
    if not sources or not targets:
        return {"error": "source or target not found", "source": source, "target": target}
    # walk from every source, stop at first target hit
    best = None
    for s in sources:
        for t in targets:
            try:
                path = nx.shortest_path(g, s, t)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                continue
            if best is None or len(path) < len(best):
                best = path
    if not best:
        return {"error": "no path", "source": source, "target": target}
    return {
        "algorithm": "shortest_path",
        "source": source,
        "target": target,
        "hops": len(best) - 1,
        "path": [g.nodes[n].get("name") for n in best],
        "edges": [
            g.get_edge_data(a, b)["rel"] for a, b in zip(best, best[1:])
        ],
    }


def weakly_connected_components() -> dict:
    g = _load_full_graph()
    comps = sorted(nx.weakly_connected_components(g), key=len, reverse=True)
    out = []
    for i, comp in enumerate(comps[:20]):
        names = sorted(g.nodes[n].get("name", "?") for n in comp)
        labels = sorted({g.nodes[n].get("label") for n in comp})
        out.append(dict(id=i, size=len(comp), labels=labels, members=names[:40]))
    return {
        "algorithm": "weakly_connected_components",
        "count": len(comps),
        "largest": len(comps[0]) if comps else 0,
        "components": out,
    }


def label_propagation() -> dict:
    """Label propagation communities (deterministic pure-Python pass)."""
    g = _load_full_graph()
    comms = _label_propagation(g)
    out = []
    for i, comm in enumerate(sorted(comms, key=len, reverse=True)[:20]):
        names = sorted(g.nodes[n].get("name", "?") for n in comm)
        labels = sorted({g.nodes[n].get("label") for n in comm})
        out.append(dict(id=i, size=len(comm), labels=labels, members=names[:40]))
    return {
        "algorithm": "label_propagation",
        "count": len(comms),
        "components": out,
    }
