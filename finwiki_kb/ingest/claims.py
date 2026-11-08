"""Rule-based candidate claim/evidence extraction (MVP).

Scope:
- sentence split
- normative/measurement cue words
- claim -> evidence -> chunk, with source span
- deterministic ids; no LLM, no truth claim

This is *candidate* extraction, not complete semantic parsing.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3

from ..graph import store

SENT = re.compile(r"[^。；;\n]+[。；;]?")
CUES = re.compile(
    r"应当|应|须|必须|不得|可以|按照|按|确认|计量|计入|披露|终止|初始计量|后续计量|摊销|折旧|税率|抵扣"
)


def _id(prefix: str, *parts: str) -> str:
    h = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{h}"


def extract_chunk(conn: sqlite3.Connection, chunk_id: str, text: str, source_path: str = "") -> dict:
    claims = 0
    for i, m in enumerate(SENT.finditer(text)):
        sent = m.group(0).strip()
        if len(sent) < 8 or not CUES.search(sent):
            continue
        claim_id = _id("CLM", chunk_id, str(i), sent)
        evidence_id = _id("EVD", claim_id)
        role = "norm" if re.search(r"应当|应|须|必须|不得|可以", sent) else "fact"
        kind = "document"

        store.add_node(conn, claim_id, "Claim", sent[:80], source_path)
        store.add_node(conn, evidence_id, "Evidence", f"{chunk_id}#s{i}", source_path)
        store.add_evidence(conn, evidence_id, claim_id, role, kind, f"{chunk_id}#s{i}", sent[:200], 1)
        store.add_edge(conn, claim_id, evidence_id, "SUPPORTS", confidence=0.5)
        store.add_edge(conn, evidence_id, chunk_id, "DERIVED_FROM", confidence=1.0)
        claims += 1
    return {"chunk": chunk_id, "claims": claims}


def extract_all(conn: sqlite3.Connection) -> dict:
    rows = list(
        conn.execute(
            """SELECT c.id, c.text, n.source_path
               FROM chunks c LEFT JOIN nodes n ON n.id = c.node_id"""
        )
    )
    total = 0
    for r in rows:
        total += extract_chunk(conn, r["id"], r["text"], r["source_path"] or "")["claims"]
    conn.commit()
    return {"chunks": len(rows), "claims": total}
