# Graphify-assisted code navigation

Reference project: https://github.com/Graphify-Labs/graphify

Graphify can index the ModelFit source and docs into a queryable graph for future development sessions. **It is a developer workflow, not part of the ModelFit application or an automatic persistent memory service.**

## Install locally (optional)
Use the official Graphify Python package as described by its maintainers:

~~~bash
uv tool install graphifyy
graphify install
~~~

In a local checkout of ModelFit, run:

~~~bash
graphify .
~~~

The external tool documents generating graphify-out/graph.html, graphify-out/graph.json and graphify-out/GRAPH_REPORT.md. You can inspect them with Graphify's own commands and browser-based viewer.

After source updates:

~~~bash
graphify update .
~~~

Generated graph data may be stale if not updated. It is not committed by default; the static Mermaid diagram in ARCHITECTURE.md and the module descriptions in AGENTS.md stay in Git for anyone to read, including future contributors and assistants.

## How to resume a development session
1. Read AGENTS.md.
2. Read docs/PROJECT_STATE.md for current work and decisions.
3. Review docs/ARCHITECTURE.md and the latest Git commits.
4. If a current graphify-out/ directory exists locally, consult the graph for code navigation and validate against actual files.
5. Update those documents when implementation changes.

**Status (2026-11-20):** Graphify integration instructions added; no generated knowledge graph is claimed or committed.
