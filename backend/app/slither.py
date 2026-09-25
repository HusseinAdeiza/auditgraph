"""Slither integration: run Slither over local Solidity source, map its
findings to SWC ids, and link them to the graph as Function-level
vulnerabilities with status='pattern' (static analysis finding).

Requires `slither` installed in PATH (pip install slither-analyzer).
"""
from __future__ import annotations

import json
import shutil
import subprocess

# Slither detector name -> canonical SWC
SLITHER_TO_SWC = {
    "reentrancy-eth": "SWC-107",
    "reentrancy-no-eth": "SWC-107",
    "arbitrary-send-eth": "SWC-101",
    "uninitialized-state": "SWC-127",
    "uninitialized-storage": "SWC-127",
    "arbitrary-send": "SWC-101",
    "unprotected-upgrade": "SWC-108",
    "unprotected-initializer": "SWC-112",
    "unchecked-low-level": "SWC-125",
    "weak-prng": "SWC-106",
    "timestamp": "SWC-122",
    "division-before-multiplication": "SWC-115",
    "unused-return": "SWC-125",
    "uninitialized-storage-map": "SWC-127",
}

SLITHER_SEVERITY = {
    "high": "critical",
    "medium": "high",
    "low": "medium",
    "informational": "low",
}


def run_slither(source_path: str, contract_name: str) -> dict:
    """Run slither and return findings mapped to SWC ids."""
    if shutil.which("slither") is None:
        return {"status": "error", "message": "slither not installed. pip install slither-analyzer"}

    proc = subprocess.run(
        ["slither", "--soljson", "solc-0.8.19+commit.7ddc701f", "--filter-path", "node_modules",
         "--json", "stdout", source_path],
        capture_output=True, text=True, timeout=180,
    )
    # slither prints json at the end of stdout
    out = proc.stdout
    start = out.find("{")
    if start < 0:
        return {"status": "error", "message": f"slither produced no JSON. stderr: {proc.stderr[-800:]}"}
    try:
        report = json.loads(out[start:])
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"bad slither JSON: {e}"}

    findings = []
    for res in report.get("results", []):
        detector = res.get("detector", "")
        swc = SLITHER_TO_SWC.get(detector)
        if not swc:
            continue
        for loc in res.get("description_locations", [])[:3]:
            findings.append(dict(
                swc=swc,
                detector=detector,
                function=loc.get("function", "unknown"),
                file=loc.get("file", ""),
                line=loc.get("line_start"),
                severity=SLITHER_SEVERITY.get(res.get("severity", "informational"), "low"),
            ))
    return {"status": "ok", "contract": contract_name, "findings": findings}


def link_findings(contract_name: str, findings: list[dict]) -> dict:
    """Upsert slither findings into the graph as Function nodes + HAS_VULNERABILITY edges."""
    from .db import query

    linked = 0
    seen = set()
    for f in findings:
        key = (f["function"], f["swc"])
        if key in seen:
            continue
        seen.add(key)
        query(
            """
            MERGE (c:Contract {name: $c})
            ON CREATE SET c.source = 'slither'
            MERGE (c)-[:HAS_FUNCTION]->(f:Function {name: $fn})
            MERGE (v:Vulnerability {swc: $swc})
            ON CREATE SET v.title = $swc, v.severity = $sev, v.category = 'static_analysis'
            MERGE (f)-[r:HAS_VULNERABILITY]->(v)
            ON CREATE SET r.source = 'slither', r.status = 'pattern'
            """,
            {"c": contract_name, "fn": f["function"], "swc": f["swc"], "sev": f["severity"]},
        )
        linked += 1
    return {"status": "ok", "linked": linked}
