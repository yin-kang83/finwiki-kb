"""Markdown ingest: Doc -> Section -> Chunk (G1) with FTS.

MVP scope:
- heading-aware sectioning
- deterministic node ids
- no claim/evidence extraction (next step)
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from ..graph import store

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")


def _id(prefix: str, *parts: str) -> str:
    h = hashlib.sha1("|".join(parts).encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{h}"


def _chunks(text: str, max_chars: int = 600) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out, buf = [], ""
    for p in paras:
        if buf and len(buf) + len(p) + 2 > max_chars:
            out.append(buf)
            buf = p
        else:
            buf = f"{buf}\n\n{p}" if buf else p
    if buf:
        out.append(buf)
    return out


def ingest_markdown(conn, path: str | Path, doc_id: str | None = None) -> dict:
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    doc_id = doc_id or _id("DOC", str(path.resolve()))
    title = path.stem
    sections: list[tuple[str, str, int]] = []  # (section_id, title, level)
    current = doc_id

    store.add_node(conn, doc_id, "Doc", title, str(path))
    chunk_no = 0
    buf: list[str] = []

    def flush():
        nonlocal buf, chunk_no
        body = "\n".join(buf).strip()
        if not body:
            return
        for piece in _chunks(body):
            chunk_no += 1
            cid = _id("CH", doc_id, str(chunk_no))
            store.add_chunk(conn, cid, current, piece)
            store.add_edge(conn, current, cid, "CONTAINS")

    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            flush()
            level, heading = len(m.group(1)), m.group(2).strip()
            if level == 1:
                title = heading
                store.add_node(conn, doc_id, "Doc", title, str(path))
                current = doc_id
            else:
                sid = _id("SEC", doc_id, str(len(sections) + 1), heading)
                store.add_node(conn, sid, "Section", heading, str(path))
                parent = doc_id
                for prev_id, _, prev_level in reversed(sections):
                    if prev_level < level:
                        parent = prev_id
                        break
                store.add_edge(conn, parent, sid, "CONTAINS")
                sections.append((sid, heading, level))
                current = sid
            continue
        buf.append(line)

    flush()
    conn.commit()
    return {"doc": doc_id, "sections": len(sections), "chunks": chunk_no}


def ingest_dir(conn, root: str | Path, pattern: str = "*.md") -> list[dict]:
    root = Path(root)
    files = [root] if root.is_file() else sorted(root.rglob(pattern))
    return [ingest_markdown(conn, p) for p in files]
