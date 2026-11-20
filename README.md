# ModelFit

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](pyproject.toml)
[![MIT License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Python tests](https://github.com/Dhruvkp07/ModelFit/actions/workflows/ci.yml/badge.svg)](https://github.com/Dhruvkp07/ModelFit/actions/workflows/ci.yml)
[![Contributions welcome](https://img.shields.io/badge/Contributions-welcome-brightgreen)](CONTRIBUTING.md)

**Check which local AI models may fit your computer.**

ModelFit is an open-source **local LLM hardware compatibility checker** for developers running AI models with **Ollama**. This lightweight Python CLI checks available system RAM and supported NVIDIA GPU VRAM, then estimates which local language models may fit. No API key or account is needed.

**Status: v0.1 alpha.** ModelFit provides approximate **memory-fit guidance**, not verified benchmarks, model quality rankings, tokens/second predictions, or guarantees.

## Why ModelFit?

- **Local AI readiness:** compare your computer's available RAM and VRAM with a sourced catalog of Ollama models.
- **Developer-friendly CLI:** use readable terminal output or JSON in scripts.
- **Community-driven:** contribute hardware backends, model records, documentation, and tests.

ModelFit is not affiliated with or endorsed by Ollama. Compatibility results are estimates, not benchmark guarantees.

## Quick start

Requires Python 3.10+ and Git.

~~~bash
pip install "git+https://github.com/Dhruvkp07/ModelFit.git"
modelfit
~~~

On Windows, use the same command in PowerShell. If the command is not found, try:

~~~bash
python -m modelfit recommend
~~~

To update later:

~~~bash
pip install --upgrade --force-reinstall "git+https://github.com/Dhruvkp07/ModelFit.git"
~~~

## Commands

~~~bash
modelfit                   # scan hardware and recommend models
modelfit scan              # show hardware only
modelfit models            # show the included public model catalog
modelfit check qwen3:4b    # assess a specific model
modelfit recommend --json  # machine-readable JSON for scripts
modelfit recommend --ram-gb 8 --vram-gb 6  # simulate available memory
~~~

**Simulation note:** --ram-gb and --vram-gb override *available* RAM/free VRAM, not installed capacity. Use them to explore another device, not to measure it.

## How recommendations work

1. Read currently available system RAM using psutil.
2. Query NVIDIA GPU free VRAM using nvidia-smi when available. Multiple GPUs are evaluated individually; their memory is **not** added.
3. Read the versioned model catalog (official Ollama download-size listings, snapshot 2026-11-20).
4. Estimate working memory with an explicit starter heuristic: **download GB × 1.2 + 0.75 GiB**.
5. Classify as **likely_gpu**, **likely_cpu**, or **unlikely**, based on currently available memory.

This deliberately simple formula is **not** actual memory profiling. Runtime overhead, context length, architecture, quantization, KV cache, drivers, memory sharing, and background programs can change the result significantly. CPU fit does not imply acceptable speed. Non-NVIDIA accelerators are not yet detected automatically. ModelFit never downloads a model or calls an AI API.

## Example

~~~text
ModelFit 0.1 | Local model memory estimator
RAM: 11.20 GiB available / 15.70 GiB total
GPU: NVIDIA ...; 5.40 GiB VRAM free

qwen3:0.6b   1.38 GiB likely_gpu   ...
qwen3:4b     3.75 GiB likely_gpu   ...
qwen3:8b     6.99 GiB likely_cpu   ...
~~~

Illustration only; your output depends on your hardware and active memory use.

## Contribute

Anyone can fork the repo, open an Issue, or propose changes through a Pull Request. Please start with [CONTRIBUTING.md](CONTRIBUTING.md). Good first contributions include additional tested GPU backends, more transparent memory estimates, improved docs, and new sourced model records.

- [Architecture and module map](docs/ARCHITECTURE.md)
- [Project handoff and current status](docs/PROJECT_STATE.md)
- [Public model sources and methodology](docs/PUBLIC_DATA.md)
- [Graphify knowledge-graph workflow](docs/GRAPHIFY.md)
- [Contributor guidelines](CONTRIBUTING.md)

ModelFit's MIT license covers **this tool's code**, not the separate licenses or terms of the third-party AI models listed in its catalog.
