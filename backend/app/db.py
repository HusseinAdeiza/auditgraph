"""FalkorDB connection helpers."""
import os

from falkordb import FalkorDB

HOST = os.getenv("FALKORDB_HOST", "127.0.0.1")
PORT = int(os.getenv("FALKORDB_PORT", "6381"))
GRAPH_NAME = os.getenv("FALKORDB_GRAPH", "audit")

_db: FalkorDB | None = None


def get_db() -> FalkorDB:
    global _db
    if _db is None:
        _db = FalkorDB(host=HOST, port=PORT)
    return _db


def get_graph():
    return get_db().select_graph(GRAPH_NAME)


def query(cypher: str, params: dict | None = None):
    return get_graph().query(cypher, params or {})


def graph_is_empty() -> bool:
    res = query("MATCH (n) RETURN count(n) AS c")
    return res.result_set[0][0] == 0


def reset_graph() -> None:
    try:
        get_graph().delete()
    except Exception:  # noqa: BLE001  # empty graph: nothing to delete
        pass
