"""Command line entry point. No accounts, API keys or downloads required."""
from __future__ import annotations

import argparse
from dataclasses import replace
import json

from .catalog import load_catalog
from .estimator import assess, recommend
from .hardware import detect_hardware

DISCLAIMER = (
    "Estimates only. Download size is not runtime memory; context length, "
    "quantization, drivers, runtime, and other processes affect actual fit. "
    "Non-NVIDIA accelerators are not automatically detected in v0.1."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="modelfit",
        description="Check which local Ollama models might fit your computer.",
    )
    sub = parser.add_subparsers(dest="command")
    for name in ("recommend", "scan", "check", "models"):
        command = sub.add_parser(name)
        command.add_argument("--json", action="store_true", help="Machine-readable output")
        if name in ("recommend", "scan", "check"):
            command.add_argument("--ram-gb", type=float, help="Override available RAM (GiB)")
            command.add_argument("--vram-gb", type=float, help="Override free VRAM (GiB)")
        if name == "check":
            command.add_argument("model", help="Exact model tag, e.g. qwen3:4b")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    command = args.command or "recommend"
    json_mode = getattr(args, "json", False)

    if command == "models":
        models = load_catalog()
        if json_mode:
            print(json.dumps(models, indent=2))
        else:
            for model in models:
                print(f"{model['name']:<20} {model['download_gb']:>6.2f} GB  {model['source']}")
        return 0

    ram = getattr(args, "ram_gb", None)
    vram = getattr(args, "vram_gb", None)
    if any(n is not None and n < 0 for n in (ram, vram)):
        parser.error("Memory overrides must be zero or positive.")

    hardware = detect_hardware()
    simulated = ram is not None or vram is not None
    if ram is not None:
        hardware = replace(hardware, available_ram_gib=ram)
    if vram is not None:
        hardware = replace(
            hardware,
            free_vram_gib=vram,
            total_vram_gib=max(vram, hardware.total_vram_gib or 0),
            gpu_name=hardware.gpu_name or ("Simulated NVIDIA GPU" if vram > 0 else None),
        )

    results = []
    if command == "check":
        matches = [m for m in load_catalog() if m["name"].lower() == args.model.lower()]
        if not matches:
            parser.error("Unknown model tag. Run 'modelfit models' for supported tags.")
        results = [assess(matches[0], hardware)]
    elif command == "recommend":
        results = recommend(load_catalog(), hardware)

    if json_mode:
        print(json.dumps({
            "hardware": hardware.to_dict(),
            "simulated": simulated,
            "results": [r.to_dict() for r in results],
            "disclaimer": DISCLAIMER,
        }, indent=2))
        return 0

    print("ModelFit 0.1 | Local model memory estimator")
    print(f"OS: {hardware.os}")
    print(f"CPU: {hardware.cpu} ({hardware.logical_cores} logical cores)")
    print(f"RAM: {hardware.available_ram_gib:.2f} GiB available / {hardware.total_ram_gib:.2f} GiB total")
    if hardware.gpu_name:
        print(f"GPU: {hardware.gpu_name}; {hardware.free_vram_gib:.2f} GiB VRAM free")
    else:
        print("GPU: not detected (NVIDIA nvidia-smi only; CPU fallback)")
    if simulated:
        print("SIMULATION: memory availability overridden by command-line values")
    if results:
        print()
        for item in results:
            print(
                f"{item.name:<20} {item.estimated_memory_gib:>6.2f} GiB "
                f"{item.status:<12} {item.reason}"
            )
    print()
    print(DISCLAIMER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
