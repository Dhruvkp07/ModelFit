"""Simple and intentionally conservative fit estimation.

Disk/download size is NOT runtime RAM use. The multiplier and fixed reserve
are approximations for a starter CLI, not measurements or benchmark claims.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math

from .hardware import Hardware

# Public Ollama sizes are expressed in decimal GB; a conservative multiplier
# and fixed allowance account roughly for runtime overhead and context.
GB_TO_GIB = 10**9 / 2**30
MEMORY_MULTIPLIER = 1.2
OVERHEAD_GIB = 0.75
MIN_GPU_HOST_RAM_GIB = 1.0


@dataclass(frozen=True)
class FitResult:
    name: str
    download_gb: float
    estimated_memory_gib: float
    status: str
    reason: str
    source: str
    ram_margin_gib: float
    vram_margin_gib: float | None

    def to_dict(self) -> dict:
        return asdict(self)


def estimated_memory_gib(download_gb: float, *, extra_memory_gib: float = 0) -> float:
    if not math.isfinite(download_gb) or download_gb <= 0:
        raise ValueError("Model download size must be finite and positive.")
    if not math.isfinite(extra_memory_gib) or extra_memory_gib < 0:
        raise ValueError("Extra memory must be finite and zero or positive.")
    required = download_gb * GB_TO_GIB * MEMORY_MULTIPLIER + OVERHEAD_GIB + extra_memory_gib
    if not math.isfinite(required):
        raise ValueError("Estimated memory exceeds the supported numeric range.")
    return required


def assess(model: dict, hardware: Hardware, *, extra_memory_gib: float = 0) -> FitResult:
    required = estimated_memory_gib(float(model["download_gb"]), extra_memory_gib=extra_memory_gib)
    available = hardware.available_ram_gib
    gpu_free = hardware.free_vram_gib
    if gpu_free is not None and gpu_free >= required and available >= MIN_GPU_HOST_RAM_GIB:
        status = "likely_gpu"
        reason = "Estimated memory fits one NVIDIA GPU's currently free VRAM."
    elif available >= required:
        status = "likely_cpu"
        reason = "Estimated memory fits currently available system RAM; CPU inference may be slow."
    else:
        status = "unlikely"
        if gpu_free is not None and gpu_free >= required and available < MIN_GPU_HOST_RAM_GIB:
            reason = "GPU VRAM may fit, but available host RAM is below the 1 GiB reserve."
        elif gpu_free is None:
            reason = "Estimated memory exceeds available RAM; supported GPU VRAM was not detected."
        else:
            reason = "Estimated memory exceeds currently available RAM and detected free VRAM."
    return FitResult(
        name=model["name"],
        download_gb=float(model["download_gb"]),
        estimated_memory_gib=required,
        status=status,
        reason=reason,
        source=model["source"],
        ram_margin_gib=available - required,
        vram_margin_gib=None if gpu_free is None else gpu_free - required,
    )


def recommend(models: list[dict], hardware: Hardware, *, extra_memory_gib: float = 0) -> list[FitResult]:
    status_order = {"likely_gpu": 0, "likely_cpu": 1, "unlikely": 2}
    results = [assess(model, hardware, extra_memory_gib=extra_memory_gib) for model in models]
    return sorted(results, key=lambda r: (status_order[r.status], r.estimated_memory_gib, r.name))
