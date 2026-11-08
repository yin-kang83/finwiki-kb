"""Read/query helpers for the MVP graph."""
from __future__ import annotations

import sqlite3


def search_chunks(conn: sqlite3.Connection, query: str, limit: int = 5) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """SELECT chunk_id, text, bm25(chunks_fts) AS rank
               FROM chunks_fts
               WHERE chunks_fts MATCH ?
               ORDER BY rank
               LIMIT ?""",
            (query, limit),
        )
    )


def evidence_chain(conn: sqlite3.Connection, claim_id: str) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """SELECT e.id, e.role, e.kind, e.ref, e.span, e.valid
               FROM evidence e
               JOIN edges ed ON ed.dst = e.id AND ed.type = 'SUPPORTS'
               WHERE ed.src = ?
               ORDER BY e.id""",
            (claim_id,),
        )
    )


def dependency_dag(conn: sqlite3.Connection, formula_id: str) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """WITH RECURSIVE deps(id) AS (
                 SELECT ?
                 UNION
                 SELECT ed.dst FROM edges ed JOIN deps d ON ed.src = d.id
                 WHERE ed.type = 'DEPENDS_ON'
               )
               SELECT id FROM deps""",
            (formula_id,),
        )
    )


def citations_of(conn: sqlite3.Connection, norm_id: str) -> list[sqlite3.Row]:
    return list(
        conn.execute(
            """SELECT ed.src, n.label
               FROM edges ed JOIN nodes n ON n.id = ed.src
               WHERE ed.dst = ? AND ed.type = 'CITES'""",
            (norm_id,),
        )
    )
