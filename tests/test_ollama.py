import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

import pytest

from modelfit import cli, ollama


@pytest.fixture
def api():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.server.requests.append(self.path)
            self.send_response(self.server.status)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(self.server.body)

    with HTTPServer(("127.0.0.1", 0), Handler) as server:
        server.status = 200
        server.body = b'{"models": []}'
        server.requests = []
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        thread.start()
        try:
            yield server
        finally:
            server.shutdown()
            thread.join()


def test_installed_uses_disk_sizes_and_selected_fit_target(api, capsys):
    exact_size = 2_031_234_567
    api.body = json.dumps({"models": [
        {"name": "custom/large:q8", "size": 6_000_000_000},
        {"model": "custom/small:q4", "size": exact_size},
        {"name": "example:cloud", "size": 500, "remote_host": "https://ollama.com"},
    ]}).encode()
    args = ["installed", "--port", str(api.server_port), "--ram-gb", "12", "--vram-gb", "4", "--json"]
    assert cli.main(args) == 0
    results = json.loads(capsys.readouterr().out)["results"]
    assert [row["name"] for row in results] == ["custom/small:q4", "custom/large:q8"]
    assert [row["status"] for row in results] == ["likely_gpu", "likely_cpu"]
    assert results[0]["size_bytes"] == exact_size
    assert results[0]["estimated_memory_gib"] == pytest.approx(exact_size / 2**30 * 1.2 + 0.75)

    assert cli.main(args + ["--target", "gpu", "--fits-only"]) == 0
    assert json.loads(capsys.readouterr().out)["results"] == [results[0]]

    assert cli.main(args + ["CUSTOM/LARGE:Q8", "--target", "cpu"]) == 0
    assert json.loads(capsys.readouterr().out)["results"] == [results[1]]
    assert api.requests == ["/api/tags"] * 3


def test_installed_distinguishes_empty_inventory_and_no_fits(api, capsys):
    args = ["installed", "--port", str(api.server_port), "--ram-gb", "0", "--vram-gb", "0"]
    assert cli.main(args) == 0
    assert "no locally installed models" in capsys.readouterr().out
    api.body = b'{"models": [{"name": "small:q4", "size": 1000000000}]}'
    assert cli.main(args + ["--fits-only"]) == 0
    assert "No installed Ollama models matched" in capsys.readouterr().out
    assert cli.main(args) == 0
    assert "Disk: 1.00 GB" in capsys.readouterr().out

    with pytest.raises(SystemExit) as exc:
        cli.main(args + ["missing:tag", "--json"])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "missing:tag" in captured.err
    assert f"modelfit installed --port {api.server_port}" in captured.err
    assert captured.out == ""


@pytest.mark.parametrize(("status", "body", "error"), [
    (302, b"", "HTTP 302"),
    (200, b"not JSON", "not valid JSON"),
    (200, b"{}", "missing a models list"),
    (200, b'{"models": [null]}', "must be an object"),
    (200, b'{"models": [{"size": 1024}]}', "missing a valid name"),
    (200, b'{"models": [{"name": "invalid", "size": true}]}', "size in bytes"),
])
def test_installed_rejects_invalid_inventory(api, status, body, error, capsys):
    api.status = status
    api.body = body
    with pytest.raises(SystemExit) as exc:
        cli.main(["installed", "--port", str(api.server_port), "--json"])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert error in captured.err
    assert captured.out == ""


def test_installed_reports_unavailable_service(monkeypatch, capsys):
    def unavailable(*_, **__):
        raise ConnectionRefusedError

    monkeypatch.setattr(ollama.HTTPConnection, "connect", unavailable)
    with pytest.raises(SystemExit) as exc:
        cli.main(["installed"])
    assert exc.value.code == 2
    error = capsys.readouterr().err
    assert "127.0.0.1:11434" in error
    assert "ollama serve" in error


def test_installed_rejects_invalid_port(capsys):
    with pytest.raises(SystemExit) as exc:
        cli.main(["installed", "--port", "65536"])
    assert exc.value.code == 2
    assert "port must be between 1 and 65535" in capsys.readouterr().err
