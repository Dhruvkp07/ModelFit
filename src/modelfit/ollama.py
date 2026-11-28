"""Read installed model sizes from the local Ollama service."""
from __future__ import annotations

from contextlib import closing
from http.client import HTTPConnection, HTTPException
import json

DEFAULT_PORT = 11434


def load_installed_models(port: int = DEFAULT_PORT) -> list[dict]:
    """Fetch local model sizes in the estimator's input format."""
    address = f"127.0.0.1:{port}"
    # A direct loopback connection avoids proxy settings and HTTP redirects.
    try:
        with closing(HTTPConnection("127.0.0.1", port, timeout=4)) as connection:
            connection.request("GET", "/api/tags")
            with connection.getresponse() as response:
                if response.status != 200:
                    raise ValueError(f"Ollama at {address} returned HTTP {response.status} for /api/tags.")
                body = response.read()
    except (OSError, HTTPException) as exc:
        raise ValueError(
            f"Could not read Ollama's model list at {address}. Start the Ollama app or run "
            "'ollama serve', and check --port if it uses a different local port."
        ) from exc

    try:
        payload = json.loads(body)
    except (ValueError, RecursionError) as exc:
        raise ValueError("Ollama's /api/tags response was not valid JSON.") from exc
    rows = payload.get("models") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        raise ValueError("Ollama's /api/tags response is missing a models list.")

    models = []
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"Ollama model entry {index} must be an object.")
        if row.get("remote_host") or row.get("remote_model"):
            continue
        name = row.get("name") or row.get("model")
        size = row.get("size")
        if not isinstance(name, str) or not name.strip() or not name.isprintable():
            raise ValueError(f"Ollama model entry {index} is missing a valid name.")
        if type(size) is not int or not 0 < size < 2**63:
            raise ValueError(f"Ollama model {name!r} is missing a valid on-disk size in bytes.")
        models.append({
            "name": name,
            "download_gb": size / 10**9,
            "source": "local Ollama",
            "size_bytes": size,
        })
    return models
