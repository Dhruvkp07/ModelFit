# Public model metadata and methodology

Snapshot date: **2026-11-20**.

The packaged catalog lists **Ollama published model-tag download sizes**, in decimal GB. Sources checked:
- Qwen3 tags: https://ollama.com/library/qwen3
- Gemma3 tags: https://ollama.com/library/gemma3
- Llama 3.2 tags: https://ollama.com/library/llama3.2

Catalog data: src/modelfit/data/models.json.

These figures are **not memory benchmarks**. Different tag variants/quantizations or later republished tags can have different sizes. Verify the current official tag pages before using sizes as current facts. Model weights, licenses and inference files are not redistributed here.

## Why a heuristic?
Model size on disk gives a rough starting point but does not account for runtime, KV cache, context, allocator fragmentation or system interference. Day-one estimator:

~~~text
estimated_memory_gib = (published_download_gb * 10**9 / 2**30 * 1.2) + 0.75 + extra_memory_gib
~~~

This formula is an openly editable heuristic, **not a validated predictive model**. The fixed overhead and factor are conservative engineering guesses. A 'likely_gpu' result requires free VRAM on one detected NVIDIA GPU plus at least 1 GiB of available system RAM. 'likely_cpu' requires sufficient available system RAM. An 'unlikely' result means neither test passed, not impossibility.

## Contributing records
Add a model's **exact Ollama tag** and **currently published download size** with a primary-source URL. Keep the snapshot date current when changing records. Do not invent performance scores or treat parameter counts as memory figures. Add tests when you change schema or fit logic.
