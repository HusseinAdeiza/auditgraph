# AuditGraph

Smart contract vulnerabilities, mapped as a graph.

Auditing is mostly tracing: who calls whom, which vulnerability patterns stack, which libraries got hit before. AuditGraph models that as nodes and edges in FalkorDB so you can query it instead of grep'ing through repos, and exports the results as a PDF report.

Built for Graph Hacks on FalkorDB.

**Live demo:** [molecules-sacred-everyone-promotes.trycloudflare.com](https://molecules-sacred-everyone-promotes.trycloudflare.com) — the full app, seeded and queryable.

## What's in the graph

- 23 contracts (Uniswap, Aave, Compound, Curve, Balancer, Maker, GMX, the bridge protocols, …)
- 76 functions with call edges between them
- 20 vulnerability patterns, aligned with the [SWC registry](https://swcregistry.io)
- 10 real exploits (DAO, bZx, Cream, KyberSwap, Beanstalk, Euler, Mango, Ronin, Poly, Wormhole) with loss figures
- 10 libraries (OpenZeppelin, Solmate, Chainlink, …)

That's 144 nodes and 222 edges. The seed is deterministic — `python -m app.seed` rebuilds the same graph every time.

## Queries

Eight Cypher templates behind the API. The interesting ones:

- `contracts_with_vulnerability` — every contract flagged for a given SWC, with severity
- `multi_vulnerability_contracts` — contracts that stack N or more patterns
- `library_risk_correlation` — which libraries carry the most real-world loss across all the protocols that use them. My favorite; it's a join you'd have to do by hand in a spreadsheet
- `cross_contract_attack_chain` — 2–6 hop `CALLS` paths that cross protocol boundaries
- `attack_path` — shortest path between two functions over call edges
- `most_exploited_functions`, `vulnerability_communities`, `full_graph_stats`

Graph algorithms on top: PageRank, betweenness centrality, shortest path, weakly connected components, label propagation.

## Stack

| | |
|---|---|
| Graph DB | FalkorDB (Docker) |
| Backend | FastAPI, Python 3.12, `falkordb` client, networkx, reportlab |
| Frontend | React + TypeScript, Vite, Tailwind v4, Cytoscape.js |
| Ingestion | Etherscan V2 (contract metadata), Slither (static analysis → SWC) |

## Run it

One container:

```bash
docker compose up --build -d
# http://localhost:8000 — API and frontend
# FalkorDB Cypher port on 6381
```

Dev setup:

```bash
docker compose up -d falkordb

cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed
uvicorn app.main:app --reload        # :8000

cd ../frontend
npm install && npm run dev           # :5173, proxies /api to :8000
```

The API auto-seeds on startup if the graph is empty. Swagger at `/docs`.

Set `ETHERSCAN_API_KEY` (free tier) for the Etherscan ingestion endpoint. Slither ingestion needs `slither` on PATH and a local Solidity path.

## How to use

Five tabs, one typical flow:

1. **Graph** — the whole seeded graph loads here. Pick a contract from the "Focus" dropdown (e.g. `KyberSwapPool`) to zoom into its neighborhood: the contract, its functions, the vulnerable ones, attached exploits, and the libraries it uses. Click any node for its properties (address, severity, loss figure, …).
2. **Queries** — the 8 templates as forms. A useful first pass:
   - `Contracts with a vulnerability` → `swc = SWC-106` → every contract flagged for price/oracle manipulation, with severity
   - `Library risk correlation` → no params → which libraries carry the most real-world loss across all protocols that use them
   - `Cross-contract attack chain` → no params → 2–6 hop call paths that start at an exploited function and leave the protocol
   Each result table is remembered and can be attached to a PDF report later.
3. **Algorithms** — PageRank (where to look first), betweenness (bridge functions), WCC (how connected the graph is), label propagation (vulnerability communities), and shortest path between two functions.
4. **Ingest** — add a live contract by Etherscan address, or run Slither over local Solidity to link static-analysis findings to the graph.
5. **Report** — pick the report subject (contract name or "full graph"), confirm which queries to include, and hit **Generate & download PDF**. You get a formatted report with the query results, PageRank scores, and graph stats — the thing you'd attach to an engagement.

API-only (skip the UI):

```bash
# run a template
curl -X POST localhost:8000/api/query -H 'Content-Type: application/json' \
  -d '{"name":"library_risk_correlation","params":{}}'

# run an algorithm
curl -X POST localhost:8000/api/algorithms/pagerank -H 'Content-Type: application/json' \
  -d '{"params":{"top":15}}'

# export a PDF
curl -X POST localhost:8000/api/report/pdf -H 'Content-Type: application/json' \
  -d '{"contract":"KyberSwapPool","queries":[{"name":"contracts_with_vulnerability","params":{"swc":"SWC-106"}}],"algorithms":["pagerank"]}' \
  -o report.pdf
```

Raw Cypher against the DB itself (FalkorDB speaks Cypher directly, port 6381):

```bash
docker exec -it auditgraph-falkordb redis-cli -p 6379 GRAPH.QUERY audit \
  "MATCH (c:Contract)-[:USES_LIBRARY]->(l:Library) RETURN c.name, l.name"
```

## API

- `GET /api/health` — liveness + node count
- `GET /api/templates` — the 8 Cypher templates
- `POST /api/query` — `{name, params}` → rows
- `GET /api/graph/full` / `GET /api/graph/neighborhood?name=&depth=` — for the Cytoscape view
- `POST /api/algorithms/{pagerank|betweenness|wcc|label_propagation|shortest_path}`
- `POST /api/ingest/etherscan` — `{address, chain_id?}` → contract node with verified/compiler/proxy status
- `POST /api/ingest/slither` — `{source_path}` → findings linked as `Function—HAS_VULNERABILITY—Vulnerability`
- `POST /api/report/pdf` — bundles the queries you ran + algorithms into a PDF
- `POST /api/admin/reset` — re-seed from scratch (requires `AUDITGRAPH_ADMIN_TOKEN` header; off unless that env var is set, so a public demo can't be wiped by a stray call)

## Scope

This is a seeded, curated graph of 23 protocols, not an indexer of all of Ethereum. The depth is in correlation and paths, not coverage. The ingestion endpoints are the seam for expanding it — point them at real addresses and repos and the graph grows without code changes.

## Notes

- FalkorDB's Cypher is close to Neo4j's but has gotchas: `shortestPath()` only works in `RETURN`, no `elementId()`, and `LIMIT $param` rejects string-typed params. All handled in the templates.
- PageRank has a pure-Python fallback so the API doesn't hard-depend on numpy/scipy.
- Seed data is compiled from public post-mortems; loss figures are as reported at the time of the incident.

## License

Code: MIT. Seed data compiled from public sources (SWC registry, exploit post-mortems) for demonstration.
