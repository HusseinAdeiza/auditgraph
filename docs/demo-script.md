# 3-minute AuditGraph demo script

**Goal:** show the before/after — an auditor's question answered in seconds by
a graph, visualized live, and exported to a PDF report.

## 0:00–0:20 — The pain (no screen, or IDE + notes)
> "When I audit a protocol, the hours go into *tracing*: who calls whom, which
> patterns stack, which libraries share risk. It's manual, it's error-prone,
> and the graph lives in my head."

## 0:20–0:50 — What AuditGraph is
Open **http://localhost:5173** (or `http://<host>:8000` in Docker).
> "AuditGraph models a smart contract vulnerability knowledge graph in
> FalkorDB — contracts, functions, SWC vulnerabilities, real exploits, and
> libraries are nodes; calls, usage, and exploitation are edges. Today's graph:
> 145 nodes, 222 edges — 24 contracts, 20 vulnerability patterns, 10 famous
> exploits."
- Point at the header badge: `graph: 144 nodes` (live from the DB).

## 0:50–1:30 — Query 1: vulnerability correlation (the wedge)
Queries tab → **Contracts with vulnerability** → SWC = `SWC-106`
(price/oracle manipulation) → Run.
> "Every contract flagged for oracle manipulation — with severity — in one
> table. No grep through a dozen repos."

## 1:30–2:10 — Query 2: library risk
Queries tab → **Library risk correlation** → Run.
> "Which libraries carry the most correlated real-world loss across protocols?
> OpenZeppelin and Chainlink top the list because the exploits hit code that
> *uses* them. That's the question no linear audit report can answer — one Cypher
> query: JOIN over USES_LIBRARY, EXPLOITED, and the loss column."

## 2:10–2:40 — Query 3: attack path + visualization
Queries tab → **Cross-contract attack chain** → Run.
> "Multi-hop call chains that start at an exploited function and cross protocol
> boundaries — e.g. EulerFinance → Uniswap → Sushiswap → 1inch → bZx."
Switch to the **Graph** tab → Focus contract = `KyberSwapPool`.
> "And the same subgraph, drawn: the contract, its functions, the vulnerable
> ones flagged, and the exploit attached. Click any node for details."
Click the KyberSwapPool node → details panel (address, chain, verified).

## 2:40–3:00 — Proof + export
Algorithms tab → **PageRank top 15** → Run (briefly).
Report tab → **Generate & download PDF**.
> "Everything I just ran — queries, results, centrality scores — bundles into a
> formatted PDF audit report, ready to attach to the engagement.
>
> **Proof metric for this build:** 24 contracts, 20 SWC patterns, 10 exploits
> ($1.7B+ in documented losses) analyzed; 8 Cypher templates; 5 graph
> algorithms; live query-to-PDF in under 3 seconds."

## Notes for the demo environment
- FalkorDB + API + frontend all running locally (ports 6381 / 8000 / 5173),
  or a single `docker compose up` on port 8000.
- Seeded data is deterministic (`python -m app.seed` from `backend/`).
- Have Etherscan V2 API key ready if you demo ingestion (free tier works).
