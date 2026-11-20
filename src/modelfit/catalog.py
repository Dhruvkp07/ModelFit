"""Versioned offline model catalog, sourced from Ollama's public library."""
from __future__ import annotations

from importlib.resources import files
import json


def load_catalog() -> list[dict]:
    path = files("modelfit").joinpath("data/models.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload["models"]
    if not isinstance(rows, list):
        raise ValueError("Model catalog must contain a models list.")
    for model in rows:
        if not isinstance(model.get("name"), str) or float(model.get("download_gb", 0)) <= 0:
            raise ValueError("Invalid model entry in catalog.")
    return rows
