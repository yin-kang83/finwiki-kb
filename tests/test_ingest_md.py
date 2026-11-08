from pathlib import Path

from finwiki_kb.graph import queries, store
from finwiki_kb.ingest import markdown


def _md(tmp_path):
    p = tmp_path / "lease.md"
    p.write_text(
        "# 租赁准则\n\n"
        "## 初始计量\n\n"
        "租赁负债应当按照租赁期开始日尚未支付的租赁付款额的现值进行初始计量。\n\n"
        "## 后续计量\n\n"
        "租赁负债应当按照实际利率法进行后续计量。\n",
        encoding="utf-8",
    )
    return p


def test_ingest_markdown(tmp_path):
    conn = store.init_db(tmp_path / "test.db")
    stats = markdown.ingest_markdown(conn, _md(tmp_path))
    assert stats["sections"] == 2
    assert stats["chunks"] >= 2
    rows = queries.search_chunks(conn, "租赁负债")
    assert rows


def test_reingest_no_duplicate(tmp_path):
    conn = store.init_db(tmp_path / "test.db")
    p = _md(tmp_path)
    markdown.ingest_markdown(conn, p)
    before = conn.execute("SELECT COUNT(*) n FROM chunks").fetchone()["n"]
    markdown.ingest_markdown(conn, p)
    after = conn.execute("SELECT COUNT(*) n FROM chunks").fetchone()["n"]
    assert before == after
    rows = queries.search_chunks(conn, "租赁负债")
    assert len(rows) == len({r["chunk_id"] for r in rows})


def test_ingest_dir(tmp_path):
    conn = store.init_db(tmp_path / "test.db")
    _md(tmp_path)
    stats = markdown.ingest_dir(conn, tmp_path)
    assert len(stats) == 1
