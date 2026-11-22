"""Read local, non-sensitive hardware information.

GPU auto-detection is intentionally limited to NVIDIA's nvidia-smi in v0.1.
Unknown accelerators are not assumed to have zero VRAM.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import math
import os
import platform
import subprocess

import psutil

GIB = 1024 ** 3


@dataclass(frozen=True)
class Hardware:
    os: str
    cpu: str
    logical_cores: int
    total_ram_gib: float
    available_ram_gib: float
    gpu_name: str | None
    total_vram_gib: float | None
    free_vram_gib: float | None

    def to_dict(self) -> dict:
        return asdict(self)


def detect_nvidia_gpu() -> tuple[str, float, float] | None:
    """Return the GPU with the most free VRAM, without adding GPUs together."""
    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.free",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=4,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None

    candidates = []
    for line in result.stdout.splitlines():
        try:
            name, total_mib, free_mib = [item.strip() for item in line.rsplit(",", 2)]
            total = float(total_mib) / 1024
            free = float(free_mib) / 1024
            if math.isfinite(total) and total > 0 and 0 <= free <= total:
                candidates.append((name, total, free))
        except (ValueError, TypeError):
            continue
    return max(candidates, key=lambda item: item[2]) if candidates else None


def detect_hardware() -> Hardware:
    memory = psutil.virtual_memory()
    gpu = detect_nvidia_gpu()
    return Hardware(
        os=platform.platform(),
        cpu=platform.processor() or platform.machine() or "Unknown CPU",
        logical_cores=os.cpu_count() or 1,
        total_ram_gib=memory.total / GIB,
        available_ram_gib=memory.available / GIB,
        gpu_name=gpu[0] if gpu else None,
        total_vram_gib=gpu[1] if gpu else None,
        free_vram_gib=gpu[2] if gpu else None,
    )
