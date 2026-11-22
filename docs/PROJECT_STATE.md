# ModelFit | living project handoff

Last updated: 2026-11-22
Phase: v0.1 alpha
Main repository: https://github.com/Dhruvkp07/ModelFit
Development branch: see current Git history

## Mission
Help anyone quickly estimate which local Ollama LLMs might fit their computer, without requiring API keys, online lookups, or a complex UI.

## Implemented in this milestone
- Pip-installable Python package and console command.
- Local system RAM detection and NVIDIA nvidia-smi GPU probe.
- Explicit, inspectable memory-fit estimator with GPU, CPU, or insufficient results.
- Dated offline catalog of 10 named Ollama model tags from public vendor pages.
- scan, models, recommend, and check commands, plus JSON output and simulation overrides.
- CI/test and contribution scaffolding.
- Durable module map and optional Graphify setup instructions.
- Custom model estimation from a user-supplied download size, finite input validation, and clearer insufficient-memory explanations.
- Unit-correct memory estimates, RAM/VRAM margins, manual extra memory allowance, and a likely-fit filter.

- Offline comparison of local single-file GGUF models from actual file sizes and v2/v3 header details.

## Exclusions / unfinished
- AMD/Intel/Apple accelerated memory detection.
- Actual llama.cpp/Ollama load tests, context-size estimation and speed benchmarks.
- Live model registry sync or automatic tag verification.
- Packaging to PyPI and signed releases.
- Web app / desktop UI.
- Persisted Graphify output: generated only after running graphify on a checkout.

## Design decisions
D001. Use Python/argparse and psutil for a small cross-platform CLI.
D002. Keep model catalog packaged and fully offline; source snapshots must be reviewable.
D003. NVIDIA nvidia-smi for initial discrete GPU VRAM detection, otherwise CPU estimate.
D004. Do not pool VRAM from several GPUs.
D005. Use one plainly documented heuristic for MVP instead of pretending to benchmark.
D006. Maintain AGENTS.md + ARCHITECTURE.md + this file as canonical context. Graphify is optional.

## First tasks for the next session
1. Review the latest commit and GitHub Actions result before expanding features.
2. Improve hardware probe coverage, starting with Apple Silicon unified memory and AMD/Intel.
3. Add unit-tested alternative estimation profiles based on model context length.
4. Record real empirical measurements and compare predictions before claiming accuracy.
5. Investigate distribution and CLI usability on Windows, Linux, macOS.

## Validation
Run: python -m pip install -e ".[dev]" && python -m pytest -q
Automated workflow: .github/workflows/ci.yml
Only mark test results as passed after observing their output; this document is not proof of a passing run.
