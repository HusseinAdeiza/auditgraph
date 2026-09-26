"""The 8 Cypher query templates AuditGraph ships with.

Each entry: id, name, description, cypher, params (name -> description).
Placeholders use $param syntax (FalkorDB parameterized Cypher).
"""

TEMPLATES: list[dict] = [
    dict(
        id="contracts_with_vulnerability",
        name="Contracts with a vulnerability",
        description="All contracts reachable through a function flagged with a given SWC.",
        cypher="""
        MATCH (f:Function)-[:HAS_VULNERABILITY]->(v:Vulnerability)
        WHERE v.swc = $swc
        MATCH (c:Contract)-[:HAS_FUNCTION]->(f)
        RETURN c.name AS contract, c.chain AS chain,
               f.name AS function, v.title AS vulnerability,
               v.severity AS severity
        ORDER BY
          CASE v.severity WHEN 'critical' THEN 4 WHEN 'high' THEN 3
               WHEN 'medium' THEN 2 ELSE 1 END DESC,
          c.name
        """,
        params={"swc": "SWC id, e.g. SWC-107 (optional: omit to list all)"},
    ),
    dict(
        id="multi_vulnerability_contracts",
        name="Multi-vulnerability contracts",
        description="Contracts carrying at least N distinct vulnerability patterns.",
        cypher="""
        MATCH (c:Contract)-[:HAS_FUNCTION]->(f:Function)-[:HAS_VULNERABILITY]->(v:Vulnerability)
        WITH c, count(DISTINCT v.swc) AS distinct_vulns, collect(DISTINCT v.swc) AS swcs
        WHERE distinct_vulns >= $min
        RETURN c.name AS contract, c.chain AS chain,
               distinct_vulns AS distinct_vulnerabilities, swcs AS swcs
        ORDER BY distinct_vulns DESC
        """,
        params={"min": "Minimum number of distinct SWC patterns (default 2)"},
    ),
    dict(
        id="attack_path",
        name="Shortest attack path",
        description="Shortest CALLS-edge path from one contract/function to another, showing the call chain an attacker can chain.",
        cypher="""
        MATCH (a:Function {name: $from}), (b:Function {name: $to})
        RETURN [n IN nodes(shortestPath((a)-[:CALLS*1..8]->(b))) | n.name] AS call_chain
        """,
        params={
            "from": "Originating function, e.g. 'bZx.executeTrade'",
            "to": "Target function, e.g. 'KyberSwapPool.convertWithSlippage'",
        },
    ),
    dict(
        id="most_exploited_functions",
        name="Most exploited functions",
        description="Functions flagged by real exploits, ranked by number of distinct exploits and correlated loss.",
        cypher="""
        MATCH (c:Contract)-[:HAS_FUNCTION]->(f:Function)-[:HAS_VULNERABILITY]->(v:Vulnerability)-[:EXPLOITED]->(e:Exploit)
        WITH c, f, v, count(DISTINCT e) AS hit_exploits, sum(DISTINCT e.loss_usd) AS total_loss
        RETURN c.name AS contract, f.name AS function, v.swc AS swc,
               v.title AS vulnerability, hit_exploits AS exploited_by,
               total_loss AS loss_usd
        ORDER BY hit_exploits DESC, total_loss DESC
        """,
        params={},
    ),
    dict(
        id="library_risk_correlation",
        name="Library risk correlation",
        description="For each shared library, total real exploit loss across the contracts that use it.",
        cypher="""
        MATCH (c:Contract)-[:USES_LIBRARY]->(l:Library)
        OPTIONAL MATCH (c)-[:HAS_FUNCTION]->(f)-[:HAS_VULNERABILITY]->(v)<-[:EXPLOITED]-(e:Exploit)
        WITH l,
             count(DISTINCT c) AS contracts_using,
             count(DISTINCT e) AS exploited_contracts,
             coalesce(sum(DISTINCT e.loss_usd), 0) AS correlated_loss_usd
        RETURN l.name AS library, l.version AS version,
               contracts_using AS contracts,
               exploited_contracts AS with_exploits,
               correlated_loss_usd AS correlated_loss_usd
        ORDER BY correlated_loss_usd DESC, contracts_using DESC
        """,
        params={},
    ),
    dict(
        id="cross_contract_attack_chain",
        name="Cross-contract attack chain",
        description="Multi-hop CALLS chains (2..6 hops) from a contract that has an exploited/patched flagged function - composite attack surfaces across protocols.",
        cypher="""
        MATCH p = (a:Contract)-[:HAS_FUNCTION]->(fa:Function)-[:CALLS*2..6]-(fb:Function)<-[:HAS_FUNCTION]-(b:Contract)
        WHERE a.name <> b.name
        MATCH (fa)-[:HAS_VULNERABILITY {status: 'exploited'}]->(v:Vulnerability)
        RETURN a.name AS source_contract, b.name AS target_contract,
               [n IN nodes(p) | n.name] AS chain,
               length(p) AS hops
        ORDER BY hops DESC
        LIMIT $limit
        """,
        params={"limit": "Max chains to return (default 25)"},
    ),
    dict(
        id="vulnerability_communities",
        name="Vulnerability communities",
        description="Label-propagation-style clustering: group contracts by overlapping vulnerability patterns.",
        cypher="""
        MATCH (c:Contract)-[:HAS_FUNCTION]->(f:Function)-[:HAS_VULNERABILITY]->(v:Vulnerability)
        WITH v, collect(DISTINCT c.name) AS contracts,
             min(CASE v.severity WHEN 'critical' THEN 4 WHEN 'high' THEN 3
                  WHEN 'medium' THEN 2 ELSE 1 END) AS min_severity
        WITH v, contracts,
             CASE min_severity WHEN 4 THEN 'critical' WHEN 3 THEN 'high'
                  WHEN 2 THEN 'medium' ELSE 'low' END AS cluster_severity
        WHERE size(contracts) >= 2
        RETURN v.swc AS community, v.title AS pattern,
               cluster_severity AS severity,
               size(contracts) AS members, contracts
        ORDER BY size(contracts) DESC
        """,
        params={},
    ),
    dict(
        id="full_graph_stats",
        name="Full graph stats",
        description="Node/edge counts by label, exploit totals, and severity distribution - the dashboard's numbers.",
        cypher="""
        MATCH (n)
        WITH labels(n)[0] AS label, count(*) AS nodes
        RETURN label, nodes
        UNION
        MATCH (a)-[r]->(b)
        WITH type(r) AS rel, count(*) AS edges
        RETURN rel AS label, edges AS nodes
        UNION
        MATCH (e:Exploit)
        RETURN 'TOTALS' AS label,
               toString(count(e)) + ' exploits / $' + toString(sum(e.loss_usd)) AS nodes
        """,
        params={},
    ),
]

BY_ID = {t["id"]: t for t in TEMPLATES}
