# ModelFit project instructions for future coding sessions

This is the **canonical entrypoint for maintainers and AI coding agents**. Read this file first, then **docs/PROJECT_STATE.md**, then **docs/ARCHITECTURE.md** before making changes.

## Purpose
An installable, offline Python CLI that estimates which local LLMs may fit available RAM/VRAM from publicly documented model download sizes. A fit estimate is **not** a benchmark or guarantee.

## Core modules
- src/modelfit/cli.py: argparse commands, human and JSON output.
- src/modelfit/hardware.py: psutil RAM, NVIDIA nvidia-smi GPU probe.
- src/modelfit/catalog.py: packaged offline JSON catalog reader.
- src/modelfit/data/models.json: public, sourced, dated model tag sizes.
- src/modelfit/estimator.py: explainable heuristic and status logic.
- tests/: isolated hardware, estimator and CLI tests.
- docs/: context, decisions, sources, architecture and Graphify workflow.

## Session checklist
1. Confirm repo and branch: **Dhruvkp07/ModelFit** only.
2. Read PROJECT_STATE, ARCHITECTURE and code touched by the task.
3. Keep logic independent of presentation. No keys, telemetry, unapproved uploads or model downloads.
4. Add/adjust tests; run python -m pytest -q.
5. Keep catalog changes source-linked and update snapshot information.
6. Update PROJECT_STATE, architecture, and relevant docs after implementation.
7. Commit at meaningful checkpoints; use a PR to merge verified changes into main.
8. If graphify-out/graph.json exists, use it for code navigation, but verify against source.
9. When Graphify is installed, run graphify update . after code changes.

## Invariants
- Never claim a model **will** fit or predict tokens/sec without actual measured evidence.
- Never add memory across separate GPUs as if it were one pool.
- Model metadata is a dated snapshot and must retain official source URLs.
- Keep v0.1 offline and dependency-light.
- Support Python >=3.10 and Windows/Linux/macOS as feasible.

## Graph knowledge
See docs/GRAPHIFY.md. Graphify's external package is optional for contributors; the human-readable documents above are the source of truth when generated graph output is absent or stale.
