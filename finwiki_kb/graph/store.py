"""SQLite-backed property graph store (MVP).

Source of truth: nodes/edges/evidence/chunks in SQLite.
Vector index is derived and not implemented here yet.
"""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_PATH = Path(__file__).resolve().parents[2] / "schema.sql"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def connect(db: str | Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db: str | Path) -> sqlite3.Connection:
    conn = connect(db)
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    conn.commit()
    return conn


def add_node(
    conn: sqlite3.Connection,
    node_id: str,
    node_type: str,
    label: str = "",
    source_path: str | None = None,
    span_start: int | None = None,
    span_end: int | None = None,
    version: str | None = None,
    hash_: str | None = None,
) -> str:
    conn.execute(
        """INSERT OR REPLACE INTO nodes
           (id,type,label,source_path,span_start,span_end,version,hash,created_at)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (node_id, node_type, label, source_path, span_start, span_end, version, hash_, now()),
    )
    return node_id


def add_edge(
    conn: sqlite3.Connection,
    src: str,
    dst: str,
    edge_type: str,
    source_span: str | None = None,
    version: str | None = None,
    confidence: float | None = None,
) -> str:
    edge_id = f"E-{uuid.uuid4().hex[:12]}"
    conn.execute(
        """INSERT INTO edges (id,src,dst,type,source_span,version,confidence,created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (edge_id, src, dst, edge_type, source_span, version, confidence, now()),
    )
    return edge_id


def add_evidence(
    conn: sqlite3.Connection,
    evidence_id: str,
    claim_id: str,
    role: str,
    kind: str,
    ref: str,
    span: str | None = None,
    valid: int = 1,
) -> str:
    conn.execute(
        """INSERT OR REPLACE INTO evidence
           (id,claim_id,role,kind,ref,span,valid,created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        (evidence_id, claim_id, role, kind, ref, span, valid, now()),
    )
    return evidence_id


def add_chunk(
    conn: sqlite3.Connection,
    chunk_id: str,
    node_id: str,
    text: str,
    span_start: int | None = None,
    span_end: int | None = None,
    version: str | None = None,
) -> str:
    conn.execute(
        """INSERT OR REPLACE INTO chunks
           (id,node_id,text,span_start,span_end,version,hash,token_count)
           VALUES (?,?,?,?,?,?,?,?)""",
        (chunk_id, node_id, text, span_start, span_end, version, None, len(text)),
    )
    conn.execute("DELETE FROM chunks_fts WHERE chunk_id = ?", (chunk_id,))
    conn.execute("INSERT INTO chunks_fts (chunk_id, text) VALUES (?, ?)", (chunk_id, text))
    return chunk_id
