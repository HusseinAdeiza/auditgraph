"""Etherscan ingestion: contract metadata + verification status -> graph nodes.

Free tier: 5 req/s, 10 req/min without an API key (EtherscanV2 supports
multiple chains via the chainid parameter).
"""
from __future__ import annotations

import httpx

ETHERSCAN_BASE = "https://api.etherscan.io/v2/api"


def ingest_contract(address: str, name: str | None = None, chain_id: int = 1, api_key: str = "") -> dict:
    """Fetch contract metadata from Etherscan and upsert into the graph."""
    params = {"module": "contract", "action": "getsourcecode", "address": address, "chainid": chain_id}
    if api_key:
        params["apikey"] = api_key

    resp = httpx.get(ETHERSCAN_BASE, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if data.get("status") != "1" or not data.get("result"):
        return {"status": "error", "message": f"Etherscan: {data.get('message', 'no result')}"}

    r = data["result"][0]
    verified = r.get("ContractName") not in (None, "Not Verified", "")
    contract_name = name or (r.get("ContractName") if verified else f"Contract_{address[:8]}")
    compiler = r.get("CompilerVersion", "unknown")
    proxy = r.get("Proxy", "0")
    implementation = r.get("Implementation") or ""

    from .db import query

    query(
        """
        MERGE (c:Contract {name: $name})
        ON CREATE SET c.address = $address, c.chain = $chain,
                      c.kind = $kind, c.protocol = 'External',
                      c.source = 'etherscan'
        SET c.address = $address,
            c.verified = $verified,
            c.compiler = $compiler,
            c.is_proxy = $is_proxy
        """,
        {
            "name": contract_name,
            "address": address,
            "chain": f"chain-{chain_id}",
            "kind": "external",
            "verified": 1 if verified else 0,
            "compiler": compiler,
            "is_proxy": 1 if proxy == "1" else 0,
        },
    )

    # proxy implementation edge
    if implementation and implementation != "0x0000000000000000000000000000000000000000":
        query(
            """
            MERGE (impl:Contract {name: $impl_name})
            ON CREATE SET impl.address = $impl_addr, impl.chain = $chain, impl.kind = 'external'
            MATCH (c:Contract {name: $name})
            MERGE (impl)-[:IMPLEMENTED_BY]->(c)
            """,
            {"impl_name": f"Impl_{implementation[:8]}", "impl_addr": implementation,
             "chain": f"chain-{chain_id}", "name": contract_name},
        )

    return {
        "status": "ok",
        "contract": contract_name,
        "address": address,
        "verified": verified,
        "compiler": compiler,
        "is_proxy": proxy == "1",
        "implementation": implementation or None,
    }
