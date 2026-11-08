from finwiki_kb.graph import queries, store
from finwiki_kb.ingest import claims, markdown


def _md(tmp_path):
    p = tmp_path / "lease.md"
    p.write_text(
        "# 租赁\n\n## 初始计量\n\n"
        "租赁负债应当按照现值进行初始计量。\n\n"
        "使用权资产应当按成本进行初始计量。\n\n"
        "租赁期不得超过二十年。\n",
        encoding="utf-8",
    )
    return p


def test_extract_claims(tmp_path):
    conn = store.init_db(tmp_path / "test.db")
    markdown.ingest_markdown(conn, _md(tmp_path))
    stats = claims.extract_all(conn)
    assert stats["claims"] >= 3
    row = conn.execute("SELECT id FROM nodes WHERE type='Claim' LIMIT 1").fetchone()
    assert row
    chain = queries.evidence_chain(conn, row["id"])
    assert len(chain) == 1
    assert chain[0]["role"] == "norm"


def test_reingest_claims_no_duplicate(tmp_path):
    conn = store.init_db(tmp_path / "test.db")
    markdown.ingest_markdown(conn, _md(tmp_path))
    claims.extract_all(conn)
    before = conn.execute("SELECT COUNT(*) n FROM nodes WHERE type='Claim'").fetchone()["n"]
    claims.extract_all(conn)
    after = conn.execute("SELECT COUNT(*) n FROM nodes WHERE type='Claim'").fetchone()["n"]
    assert before == after
    rows = conn.execute("SELECT COUNT(*) n FROM evidence").fetchone()["n"]
    assert rows == before
