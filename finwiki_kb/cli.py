"""CLI for the finwiki-kb MVP."""
from __future__ import annotations

import argparse

from .graph import queries, store


def ingest_demo(conn) -> None:
    store.add_node(conn, "DOC1", "Doc", "租赁准则", "demo/lease.md")
    store.add_node(conn, "SEC1", "Section", "租赁负债初始计量", "demo/lease.md", 0, 100)
    store.add_chunk(
        conn, "CH1", "SEC1",
        "租赁负债应当按照租赁期开始日尚未支付的租赁付款额的现值进行初始计量。",
        0, 100, "v1",
    )
    store.add_node(conn, "CLAIM1", "Claim", "租赁负债按现值初始计量")
    store.add_node(conn, "EV1", "Evidence", "租赁准则第 14 条")
    store.add_evidence(conn, "EV1", "CLAIM1", "norm", "regulation", "租赁准则第 14 条", "第 14 条")
    store.add_edge(conn, "DOC1", "SEC1", "CONTAINS")
    store.add_edge(conn, "SEC1", "CH1", "CONTAINS")
    store.add_edge(conn, "CLAIM1", "EV1", "SUPPORTS")
    conn.commit()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="finwiki-kb")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="create database")
    p_init.add_argument("--db", required=True)

    p_ing = sub.add_parser("ingest", help="ingest demo document")
    p_ing.add_argument("--db", required=True)
    p_ing.add_argument("--demo", action="store_true")

    p_search = sub.add_parser("search", help="FTS search")
    p_search.add_argument("--db", required=True)
    p_search.add_argument("--q", required=True)
    p_search.add_argument("--limit", type=int, default=5)

    p_ev = sub.add_parser("evidence", help="evidence chain")
    p_ev.add_argument("--db", required=True)
    p_ev.add_argument("--claim", required=True)

    p_dep = sub.add_parser("deps", help="dependency DAG placeholder")
    p_dep.add_argument("--db", required=True)
    p_dep.add_argument("--formula", required=True)

    args = parser.parse_args(argv)
    if args.cmd == "init":
        store.init_db(args.db)
        print(f"initialized {args.db}")
        return 0
    if args.cmd == "ingest":
        conn = store.init_db(args.db)
        if args.demo:
            ingest_demo(conn)
            print("demo ingested")
        else:
            print("only --demo is implemented in MVP")
        return 0
    if args.cmd == "search":
        conn = store.init_db(args.db)
        for row in queries.search_chunks(conn, args.q, args.limit):
            print(f"{row['chunk_id']}\t{row['text'][:80]}")
        return 0
    if args.cmd == "evidence":
        conn = store.init_db(args.db)
        for row in queries.evidence_chain(conn, args.claim):
            print(f"{row['id']}\t{row['role']}\t{row['kind']}\t{row['ref']}")
        return 0
    if args.cmd == "deps":
        conn = store.init_db(args.db)
        for row in queries.dependency_dag(conn, args.formula):
            print(row["id"])
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
