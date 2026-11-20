import json

import pytest

from modelfit import cli
from modelfit.hardware import Hardware


def mock_machine():
    return Hardware("TestOS", "Test CPU", 4, 16, 8, None, None, None)


def test_models_prints_bundled_catalog(capsys):
    assert cli.main(["models"]) == 0
    assert "qwen3:4b" in capsys.readouterr().out


def test_recommend_json_with_simulated_memory(monkeypatch, capsys):
    monkeypatch.setattr(cli, "detect_hardware", mock_machine)
    assert cli.main(["recommend", "--ram-gb", "8", "--vram-gb", "4", "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["simulated"] is True
    assert result["hardware"]["free_vram_gib"] == 4
    assert any(r["name"] == "qwen3:4b" for r in result["results"])


def test_scan_without_catalog(monkeypatch, capsys):
    monkeypatch.setattr(cli, "detect_hardware", mock_machine)
    assert cli.main(["scan", "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["results"] == []
    assert result["hardware"]["available_ram_gib"] == 8


def test_check_specific_model(monkeypatch, capsys):
    monkeypatch.setattr(cli, "detect_hardware", mock_machine)
    assert cli.main(["check", "qwen3:4b", "--json"]) == 0
    output = json.loads(capsys.readouterr().out)
    assert len(output["results"]) == 1
    assert output["results"][0]["name"] == "qwen3:4b"


def test_unknown_model_errors(monkeypatch):
    monkeypatch.setattr(cli, "detect_hardware", mock_machine)
    with pytest.raises(SystemExit) as exc:
        cli.main(["check", "not-a-model"])
    assert exc.value.code == 2


def test_negative_override_errors(monkeypatch):
    monkeypatch.setattr(cli, "detect_hardware", mock_machine)
    with pytest.raises(SystemExit) as exc:
        cli.main(["scan", "--ram-gb", "-1"])
    assert exc.value.code == 2
