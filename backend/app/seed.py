"""Seed the AuditGraph graph from the data modules (idempotent)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data.contracts import AUDITORS, CONTRACTS, FUNCTIONS, LIBRARIES, USES_LIBRARY  # noqa: E402
from app.data.exploits import EXPLOITS  # noqa: E402
from app.data.vulnerabilities import SEVERITY_RANK, VULNERABILITIES  # noqa: E402
from app.db import get_graph, reset_graph  # noqa: E402

SEED_VERSION = os.getenv("SEED_VERSION", "1")


def _esc(v: str) -> str:
    return v.replace("\\", "\\\\").replace('"', '\\"')


def build_statements() -> list[str]:
    st: list[str] = []

    for v in VULNERABILITIES:
        st.append(
            f'CREATE (v:Vulnerability {{swc: "{_esc(v["swc"])}", '
            f'title: "{_esc(v["title"])}", severity: "{_esc(v["severity"])}", '
            f'category: "{_esc(v["category"])}", '
            f'description: "{_esc(v["description"])}", '
            f'mitigation: "{_esc(v["mitigation"])}", '
            f'severity_rank: {SEVERITY_RANK[v["severity"]]}}})'
        )

    for e in EXPLOITS:
        st.append(
            f'CREATE (e:Exploit {{name: "{_esc(e["name"])}", year: {e["year"]}, '
            f'loss_usd: {e["loss_usd"]}, chain: "{_esc(e["chain"])}", '
            f'summary: "{_esc(e["summary"])}"}})'
        )

    for c in CONTRACTS:
        addr = c.get("address") or "unknown"
        st.append(
            f'CREATE (c:Contract {{name: "{_esc(c["name"])}", '
            f'address: "{_esc(addr)}", chain: "{_esc(c["chain"])}", '
            f'kind: "{_esc(c["kind"])}", protocol: "{_esc(c["protocol"])}"}})'
        )

    for l in LIBRARIES:
        st.append(
            f'CREATE (l:Library {{name: "{_esc(l["name"])}", '
            f'version: "{_esc(l["version"])}", usage: "{_esc(l["usage"])}"}})'
        )

    for auditor, contract in AUDITORS:
        st.append(
            f'MERGE (a:Auditor {{name: "{_esc(auditor)}"}}) '
            f'MERGE (c:Contract {{name: "{_esc(contract)}"}}) '
            f'CREATE (a)-[:AUDITED]->(c)'
        )

    for lib, contract in USES_LIBRARY:
        st.append(
            f'MATCH (c:Contract {{name: "{_esc(contract)}"}}), '
            f'(l:Library {{name: "{_esc(lib)}"}}) '
            f'CREATE (c)-[:USES_LIBRARY]->(l)'
        )

    # Pass 1: create all Function nodes
    for fkey, (contract, desc, calls, vulns) in FUNCTIONS.items():
        st.append(
            f'MATCH (c:Contract {{name: "{_esc(contract)}"}}) '
            f'CREATE (c)-[:HAS_FUNCTION]->'
            f'(f:Function {{name: "{_esc(fkey)}", '
            f'description: "{_esc(desc)}"}})'
        )

    # Pass 2: vulnerability edges
    for fkey, (contract, desc, calls, vulns) in FUNCTIONS.items():
        for swc, source, status in vulns:
            st.append(
                f'MATCH (f:Function {{name: "{_esc(fkey)}"}}), '
                f'(v:Vulnerability {{swc: "{_esc(swc)}"}}) '
                f'CREATE (f)-[:HAS_VULNERABILITY {{source: "{_esc(source)}", '
                f'status: "{_esc(status)}"}}]->(v)'
            )

    # Pass 3: CALLS edges (both endpoints guaranteed to exist now)
    for fkey, (contract, desc, calls, vulns) in FUNCTIONS.items():
        for target in calls:
            st.append(
                f'MATCH (f:Function {{name: "{_esc(fkey)}"}}), '
                f'(g:Function {{name: "{_esc(target)}"}}) '
                f'CREATE (f)-[:CALLS]->(g)'
            )

    # Exploit -> Vulnerability (EXPLOITED) and Exploit -> Contract (TARGET)
    for e in EXPLOITS:
        for swc in e["techniques"]:
            st.append(
                f'MATCH (e:Exploit {{name: "{_esc(e["name"])}"}}), '
                f'(v:Vulnerability {{swc: "{_esc(swc)}"}}) '
                f'CREATE (v)-[:EXPLOITED]->(e)'
            )
        st.append(
            f'MATCH (e:Exploit {{name: "{_esc(e["name"])}"}}), '
            f'(c:Contract {{name: "{_esc(e["target"])}"}}) '
            f'CREATE (c)-[:TARGET_OF]->(e)'
        )

    return st


def seed(force: bool = False) -> dict:
    if force:
        reset_graph()
    g = get_graph()
    # idempotency guard
    n = g.query("MATCH (n) RETURN count(n) AS c").result_set[0][0]
    if n > 0 and not force:
        return {"status": "already_seeded", "nodes": int(n)}
    stmts = build_statements()
    ok = 0
    for s in stmts:
        g.query(s)
        ok += 1
    res = g.query("MATCH (n) RETURN count(n) AS c").result_set[0][0]
    eres = g.query("MATCH ()-[r]->() RETURN count(r) AS c").result_set[0][0]
    return {"status": "seeded", "statements": ok, "nodes": int(res), "edges": int(eres)}


if __name__ == "__main__":
    import json

    print(json.dumps(seed(force="--force" in sys.argv), indent=2))
