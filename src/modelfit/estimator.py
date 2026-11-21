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

    def to_dict(self) -> dict:
        return asdict(self)


def estimated_memory_gib(download_gb: float) -> float:
    if not math.isfinite(download_gb) or download_gb <= 0:
        raise ValueError("Model download size must be finite and positive.")
    return round(download_gb * MEMORY_MULTIPLIER + OVERHEAD_GIB, 2)


def assess(model: dict, hardware: Hardware) -> FitResult:
    required = estimated_memory_gib(float(model["download_gb"]))
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
    )


def recommend(models: list[dict], hardware: Hardware) -> list[FitResult]:
    status_order = {"likely_gpu": 0, "likely_cpu": 1, "unlikely": 2}
    results = [assess(model, hardware) for model in models]
    return sorted(results, key=lambda r: (status_order[r.status], r.estimated_memory_gib, r.name))
