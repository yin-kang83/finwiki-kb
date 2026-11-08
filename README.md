# finwiki-kb

**FinWiki Knowledge Base** — 文档图、证据图与向量索引的轻量知识库。

> 状态：M1 骨架 + Markdown ingest；向量索引/claim 抽取未实现。
> 定位：可定位、可回指、可复算的知识底座；不是“图=证明”，不是生产级审计系统。

## 为什么做

普通 RAG 把文档切 chunk、做向量、取 top-k。它提高召回，但回答不了：

```text
这条结论凭什么？
这个公式依赖什么？
这条准则被哪些文档引用？
两个结论是否冲突？
```

`finwiki-kb` 把这些问题显式化成图：

```text
G1 文档结构图：章 → 节 → 段 → 表
G2 语义图：概念/科目/税种/主体
G3 检索图：chunk/查询的相似边（派生索引）
G4 计算图：公式/输入/中间量/结果的依赖 DAG
G5 证据图：结论 → 证据 → 原文 span
```

核心原则：

```text
每条边只保证它自己的语义；
检索到 ≠ 蕴含；
相似 ≠ 适用；
图上有边 ≠ 结论为真。
```

## 是什么

```text
SQLite：source of truth（文档/章节/claim/evidence/公式）
图：邻接表（nodes/edges），不是 Neo4j
向量：派生索引（sqlite-vec / FAISS），可重建
检索：FTS5 + 向量 + metadata + 图过滤
版本：append-only + supersede
```

## 不是什么

```text
不是通用知识图谱平台
不是自动本体学习
不是图神经网络
不是“上 Neo4j 就智能”
不是“可审计/生产可用”的承诺
```

## 架构

```text
原文 / PDF / Markdown
  → 解析标题（G1）
  → 切 chunk（heading-aware，带 span/version）
  → 抽取 claim/evidence（G5，带 role/kind/ref/span）
  → 解析公式/计算 trace（G4）
  → SQLite nodes/edges/evidence
  → 向量索引（G3，派生）
  → hybrid retrieve
  → 图过滤/扩展
  → 返回 chunk + span + 证据链
```

## 数据模型

节点：

```text
Doc / Section / Chunk
Concept / Entity / Norm
Claim / Evidence
Formula / Result / Task
```

边：

```text
CONTAINS      文档 → 章节 → 段
CITES         文档 → 准则/论文
SUPPORTS      Claim → Evidence
DERIVED_FROM  Result → 输入/中间量
DEPENDS_ON    Formula → Formula/输入
CONTRADICTS   Claim ↔ Claim
SAME_AS       Concept ↔ Concept
VERSION_OF    Node → 旧版
```

最低要求：

```text
每条边有 source/version/span；
没有来源的边不入库；
LLM 抽取的边标 confidence，不默认 1.0。
```

## 目录（计划）

```text
finwiki-kb/
  README.md
  schema.sql
  ingest/
    parse_md.py
    chunk.py
    claims.py
    formulas.py
  graph/
    store.py          # nodes/edges/evidence
    queries.py        # 证据链/依赖/引用/冲突
  retrieval/
    fts.py
    vector.py         # sqlite-vec / FAISS
    hybrid.py
  eval/
    recall.py
    audit.py
  cli.py
  tests/
```

## 快速开始（MVP，待实现）

```bash
# 1 建库
python -m finwiki_kb.cli init --db finwiki.db

# 2 入库
python -m finwiki_kb.cli ingest --db finwiki.db --docs ./docs

# 3 检索
python -m finwiki_kb.cli search --db finwiki.db --q "租赁负债初始计量"

# 4 证据链
python -m finwiki_kb.cli evidence --db finwiki.db --claim C001

# 5 依赖
python -m finwiki_kb.cli deps --db finwiki.db --formula F001
```

> 以上命令是目标接口，不是当前可运行状态。

## 评测

```text
recall@k / MRR / nDCG
context tokens / latency
citation span 对齐率
证据链完整率
false support（相似但无蕴含）
```

对照：

```text
FTS only
vector only
hybrid
hybrid + graph filter
```

## 路线图

```text
M0 设计 + schema + 10 份文档
M1 SQLite 图 + FTS + 证据链
M2 向量索引 + hybrid
M3 评测 120 题 × 4 条件
M4 版本/增量/冲突检测
```

## 限制

```text
图构建依赖人工/LLM，边可能有错；
chunk 边界可能错；
embedding 模型会漂移；
相似边不是蕴含边；
当前无多租户/权限/生产审计。
```

## 一句话

```text
先把“文档→章节→claim→evidence→formula”这条链存对；
图算法和向量是后话，边语义先要对。
```
