from finwiki_kb.cli import ingest_demo
from finwiki_kb.graph import queries, store


def test_init_and_demo(tmp_path):
    db = tmp_path / "test.db"
    conn = store.init_db(db)
    ingest_demo(conn)
    nodes = conn.execute("SELECT COUNT(*) AS n FROM nodes").fetchone()["n"]
    edges = conn.execute("SELECT COUNT(*) AS n FROM edges").fetchone()["n"]
    assert nodes == 4
    assert edges == 3


def test_evidence_chain(tmp_path):
    conn = store.init_db(tmp_path / "test.db")
    ingest_demo(conn)
    rows = queries.evidence_chain(conn, "CLAIM1")
    assert len(rows) == 1
    assert rows[0]["role"] == "norm"


def test_search(tmp_path):
    conn = store.init_db(tmp_path / "test.db")
    ingest_demo(conn)
    rows = queries.search_chunks(conn, "租赁负债")
    assert rows, "expected at least one FTS hit"


def test_reingest_no_duplicate(tmp_path):
    conn = store.init_db(tmp_path / "test.db")
    ingest_demo(conn)
    ingest_demo(conn)
    rows = queries.search_chunks(conn, "租赁负债")
    assert len(rows) == 1
