-- finwiki-kb schema v0.1
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS nodes (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  label TEXT,
  source_path TEXT,
  span_start INTEGER,
  span_end INTEGER,
  version TEXT,
  hash TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS edges (
  id TEXT PRIMARY KEY,
  src TEXT NOT NULL,
  dst TEXT NOT NULL,
  type TEXT NOT NULL,
  source_span TEXT,
  version TEXT,
  confidence REAL,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS evidence (
  id TEXT PRIMARY KEY,
  claim_id TEXT NOT NULL,
  role TEXT NOT NULL,
  kind TEXT NOT NULL,
  ref TEXT NOT NULL,
  span TEXT,
  valid INTEGER DEFAULT 1,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS versions (
  id TEXT PRIMARY KEY,
  node_id TEXT NOT NULL,
  old_hash TEXT,
  new_hash TEXT,
  reason TEXT,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS chunks (
  id TEXT PRIMARY KEY,
  node_id TEXT NOT NULL,
  text TEXT NOT NULL,
  span_start INTEGER,
  span_end INTEGER,
  version TEXT,
  hash TEXT,
  token_count INTEGER
);

CREATE TABLE IF NOT EXISTS embeddings (
  chunk_id TEXT NOT NULL,
  model TEXT NOT NULL,
  dim INTEGER NOT NULL,
  vector BLOB NOT NULL,
  created_at TEXT,
  PRIMARY KEY (chunk_id, model)
);

CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src, type);
CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst, type);
CREATE INDEX IF NOT EXISTS idx_evidence_claim ON evidence(claim_id);

CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
  chunk_id UNINDEXED,
  text,
  tokenize='trigram'
);
