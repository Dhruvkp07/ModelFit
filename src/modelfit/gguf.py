"""Identify local GGUF model files and measure their size without loading weights."""
from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import struct

# GGUF v2/v3 fixed header: magic, version, tensor count, metadata count.
_HEADER_SIZE = 24
_SPLIT_NAME = re.compile(r"(.+)-([0-9]{5})(-of-([0-9]{5})\.gguf)", re.IGNORECASE)


def inspect_gguf(path: Path) -> dict:
    """Return size and header details for a single-file model candidate."""
    if not path.is_file():
        raise ValueError("Expected a regular GGUF file.")
    with path.open("rb") as model_file:
        info = os.fstat(model_file.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("Expected a regular GGUF file.")
        header = model_file.read(_HEADER_SIZE)

    if len(header) != _HEADER_SIZE or header[:4] != b"GGUF":
        raise ValueError("Missing or incomplete GGUF header.")

    version, tensors, metadata = struct.unpack("<IQQ", header[4:])
    if version == 3 << 24:
        version, tensors, metadata = struct.unpack(">IQQ", header[4:])
    if version not in (2, 3):
        raise ValueError("Unsupported GGUF version. Expected version 2 or 3.")
    # Each tensor descriptor needs at least 24 bytes, each metadata entry 13.
    if not tensors or tensors * 24 + metadata * 13 >= info.st_size - _HEADER_SIZE:
        raise ValueError("GGUF header indicates missing tensor data or a truncated file.")
    return {
        "name": path.name,
        "download_gb": info.st_size / 10**9,
        "source": "local GGUF file",
        "path": str(path),
        "size_bytes": info.st_size,
        "gguf_version": version,
        "tensor_count": tensors,
    }


def gguf_model_key(path: Path) -> Path:
    """Use the first shard as the identity of a split model."""
    match = _SPLIT_NAME.fullmatch(path.name)
    if not match:
        return path.resolve()
    stem, index, suffix, count = match.groups()
    if not 1 <= int(index) <= int(count):
        raise ValueError("Split GGUF shard index is outside the declared range.")
    return path.parent.resolve() / f"{stem}-00001{suffix}"


def inspect_gguf_model(path: Path) -> dict:
    """Inspect one local model, discovering conventionally named sibling shards."""
    match = _SPLIT_NAME.fullmatch(path.name)
    if not match:
        return inspect_gguf(path)

    stem, _, suffix, count = match.groups()
    gguf_model_key(path)
    shards = []
    seen_files = set()
    for index in range(1, int(count) + 1):
        shard = path.with_name(f"{stem}-{index:05d}{suffix}")
        try:
            info = shard.stat()
            identity = (info.st_dev, info.st_ino)
            if info.st_ino and identity in seen_files:
                raise ValueError("Duplicate shard file.")
            seen_files.add(identity)
            shards.append(inspect_gguf(shard))
        except (OSError, ValueError) as exc:
            raise ValueError(f"Split GGUF shard {shard.name}: {exc}") from exc

    version = shards[0]["gguf_version"]
    if any(shard["gguf_version"] != version for shard in shards):
        raise ValueError("Split GGUF shards use different GGUF versions.")
    size = sum(shard["size_bytes"] for shard in shards)
    return {
        "name": f"{stem}.gguf",
        "download_gb": size / 10**9,
        "source": "local split GGUF",
        "path": shards[0]["path"],
        "size_bytes": size,
        "gguf_version": version,
        "tensor_count": sum(shard["tensor_count"] for shard in shards),
        "shard_count": len(shards),
        "shards": shards,
    }
