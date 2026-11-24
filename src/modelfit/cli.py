"""Command line entry point. No accounts, API keys or downloads required."""
from __future__ import annotations

import argparse
from dataclasses import replace
import json
import math
from pathlib import Path

from .catalog import load_catalog
from .estimator import assess, recommend
from .gguf import gguf_model_key, inspect_gguf_model
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
    for name in ("recommend", "scan", "check", "models", "estimate", "gguf"):
        command = sub.add_parser(name)
        command.add_argument("--json", action="store_true", help="Machine-readable output")
        if name in ("recommend", "scan", "check", "estimate", "gguf"):
            command.add_argument("--ram-gb", type=float, help="Override available RAM (GiB)")
            command.add_argument("--vram-gb", type=float, help="Override free VRAM (GiB)")
        if name in ("recommend", "check", "estimate", "gguf"):
            command.add_argument(
                "--target", choices=("auto", "cpu", "gpu"), default="auto",
                help="Evaluate CPU or full-GPU inference only (default: auto)",
            )
            command.add_argument(
                "--extra-memory-gib", type=float, default=0,
                help="Add a memory allowance in GiB for your runtime or context",
            )
        if name == "recommend":
            command.add_argument("--fits-only", action="store_true", help="Hide unlikely fits")
        if name == "check":
            command.add_argument("model", help="Exact model tag, e.g. qwen3:4b")
        if name == "estimate":
            command.add_argument("size_gb", type=float, help="Model download size in decimal GB")
            command.add_argument("--name", default="custom model", help="Label for this estimate")
        if name == "gguf":
            command.add_argument("files", type=Path, nargs="+", help="Local GGUF models or any shard of a split model")
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
    if any(n is not None and (not math.isfinite(n) or n < 0) for n in (ram, vram)):
        parser.error("Memory overrides must be finite and zero or positive.")
    if command == "estimate" and (not math.isfinite(args.size_gb) or args.size_gb <= 0):
        parser.error("Model download size must be finite and positive.")

    extra_memory = getattr(args, "extra_memory_gib", 0)
    if not math.isfinite(extra_memory) or extra_memory < 0:
        parser.error("Extra memory must be finite and zero or positive.")

    local_models = []
    if command == "gguf":
        seen_models = set()
        for path in args.files:
            try:
                key = gguf_model_key(path)
                if key not in seen_models:
                    local_models.append(inspect_gguf_model(path))
                    seen_models.add(key)
            except (OSError, RuntimeError, ValueError) as exc:
                parser.error(f"{path}: {exc}")

    hardware = detect_hardware()
    simulated = ram is not None or vram is not None
    if ram is not None:
        hardware = replace(hardware, available_ram_gib=ram, total_ram_gib=max(ram, hardware.total_ram_gib))
    if vram is not None:
        hardware = replace(
            hardware,
            free_vram_gib=vram,
            total_vram_gib=max(vram, hardware.total_vram_gib or 0),
            gpu_name=hardware.gpu_name or ("Simulated NVIDIA GPU" if vram > 0 else None),
        )

    target = getattr(args, "target", "auto")
    results = []
    if command == "check":
        matches = [m for m in load_catalog() if m["name"].lower() == args.model.lower()]
        if not matches:
            parser.error("Unknown model tag. Run 'modelfit models' for supported tags.")
        results = [assess(matches[0], hardware, extra_memory_gib=extra_memory, target=target)]
    elif command == "recommend":
        results = recommend(load_catalog(), hardware, extra_memory_gib=extra_memory, target=target)
        if getattr(args, "fits_only", False):
            results = [item for item in results if item.status != "unlikely"]
    elif command == "estimate":
        model = {"name": args.name, "download_gb": args.size_gb, "source": "user supplied"}
        try:
            results = [assess(model, hardware, extra_memory_gib=extra_memory, target=target)]
        except ValueError as exc:
            parser.error(str(exc))
    elif command == "gguf":
        results = [
            assess(model, hardware, extra_memory_gib=extra_memory, target=target)
            for model in local_models
        ]

    if json_mode:
        payload = {
            "hardware": hardware.to_dict(),
            "simulated": simulated,
            "extra_memory_gib": extra_memory,
            "results": [r.to_dict() for r in results],
            "disclaimer": DISCLAIMER,
        }
        if target != "auto":
            payload["target"] = target
        if local_models:
            payload["gguf_files"] = local_models
        print(json.dumps(payload, indent=2))
        return 0

    print("ModelFit 0.1 | Local model memory estimator")
    print(f"OS: {hardware.os}")
    print(f"CPU: {hardware.cpu} ({hardware.logical_cores} logical cores)")
    print(f"RAM: {hardware.available_ram_gib:.2f} GiB available / {hardware.total_ram_gib:.2f} GiB total")
    if hardware.gpu_name:
        print(f"GPU: {hardware.gpu_name}; {hardware.free_vram_gib:.2f} GiB VRAM free")
    elif target == "gpu":
        if vram is None:
            print("GPU: not detected (NVIDIA nvidia-smi only)")
        else:
            print(f"GPU: Simulated NVIDIA GPU; {vram:.2f} GiB VRAM free")
    else:
        print("GPU: not detected (NVIDIA nvidia-smi only; CPU fallback)")
    if simulated:
        print("SIMULATION: memory availability overridden by command-line values")
    if target != "auto":
        print(f"Fit target: {target.upper()}")
    if extra_memory:
        print(f"Extra memory allowance: {extra_memory:g} GiB")
    if command == "recommend" and not results:
        print("No catalog models matched the selected fit filter.")
    if results:
        print()
        for index, item in enumerate(results):
            if local_models:
                model = local_models[index]
                details = f"{model['path']} | GGUF v{model['gguf_version']} | {model['size_bytes']:,} bytes"
                if "shard_count" in model:
                    details += f" across {model['shard_count']} shards"
                print(details)
            vram_margin = (
                "unknown" if item.vram_margin_gib is None else f"{item.vram_margin_gib:+.2f} GiB"
            )
            print(
                f"{item.name:<20} {item.estimated_memory_gib:>6.2f} GiB "
                f"{item.status:<12} {item.reason}"
            )
            print(f"  Memory margin: RAM {item.ram_margin_gib:+.2f} GiB, VRAM {vram_margin}")
    print()
    print(DISCLAIMER)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
