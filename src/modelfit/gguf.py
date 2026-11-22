"""Identify local GGUF model files and measure their size without loading weights."""
from __future__ import annotations

import os
from pathlib import Path
import re
import stat
import struct

# GGUF v2/v3 fixed header: magic, version, tensor count, metadata count.
_HEADER_SIZE = 24
_SPLIT_NAME = re.compile(r"-\d{5}-of-\d{5}\.gguf$", re.IGNORECASE)


def inspect_gguf(path: Path) -> dict:
    """Return size and header details for a single-file model candidate."""
    if _SPLIT_NAME.search(path.name):
        raise ValueError("Split GGUF files require an estimate for the combined size of all shards.")
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
