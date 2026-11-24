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


def test_estimate_custom_model(monkeypatch, capsys):
    monkeypatch.setattr(cli, "detect_hardware", mock_machine)
    assert cli.main(["estimate", "2", "--name", "my-model", "--ram-gb", "8", "--json"]) == 0
    result = json.loads(capsys.readouterr().out)["results"][0]
    assert result["name"] == "my-model"
    assert result["estimated_memory_gib"] == pytest.approx(2_000_000_000 / 2**30 * 1.2 + 0.75)
    assert result["status"] == "likely_cpu"


@pytest.mark.parametrize("args", [
    ["scan", "--ram-gb", "nan"], ["scan", "--vram-gb", "inf"],
    ["estimate", "nan"], ["estimate", "0"], ["estimate", "inf"],
])
def test_reject_non_finite_and_invalid_inputs(args):
    with pytest.raises(SystemExit) as exc:
        cli.main(args)
    assert exc.value.code == 2


def test_fits_only_respects_extra_memory_allowance(monkeypatch, capsys):
    monkeypatch.setattr(cli, "detect_hardware", mock_machine)
    args = ["recommend", "--fits-only", "--ram-gb", "3", "--vram-gb", "0", "--json"]
    assert cli.main(args) == 0
    baseline = json.loads(capsys.readouterr().out)
    assert baseline["results"]
    assert all(row["status"] == "likely_cpu" for row in baseline["results"])

    assert cli.main(args + ["--extra-memory-gib", "3"]) == 0
    reserved = json.loads(capsys.readouterr().out)
    assert reserved["extra_memory_gib"] == 3
    assert reserved["results"] == []


def test_estimate_rejects_overflow(monkeypatch, capsys):
    monkeypatch.setattr(cli, "detect_hardware", mock_machine)
    with pytest.raises(SystemExit) as exc:
        cli.main(["estimate", "1.7e308", "--json"])
    assert exc.value.code == 2
    assert "numeric range" in capsys.readouterr().err


def test_gguf_compares_local_models_in_input_order(tmp_path, monkeypatch, capsys):
    import struct

    monkeypatch.setattr(cli, "detect_hardware", mock_machine)
    paths = [tmp_path / "models with spaces" / "large.gguf", tmp_path / "small.gguf"]
    paths[0].parent.mkdir()
    for path, size, version, endian in zip(paths, (4096, 1024), (3, 2), (">", "<")):
        header = b"GGUF" + struct.pack(f"{endian}IQQ", version, 1, 0)
        path.write_bytes(header.ljust(size, b"\x00"))

    assert cli.main(["gguf", *map(str, paths), "--extra-memory-gib", "1", "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert [file["size_bytes"] for file in report["gguf_files"]] == [4096, 1024]
    assert [file["gguf_version"] for file in report["gguf_files"]] == [3, 2]
    assert [row["name"] for row in report["results"]] == ["large.gguf", "small.gguf"]
    assert report["results"][0]["estimated_memory_gib"] > report["results"][1]["estimated_memory_gib"]
    assert report["results"][1]["estimated_memory_gib"] > 1.75


@pytest.mark.parametrize(("name", "content", "error"), [
    ("model.gguf", b"GGUF", "incomplete GGUF header"),
    ("model.gguf", b"GGUF\x03" + b"\x00" * 19, "truncated file"),
    ("model-00001-of-00002.gguf", b"", "Split GGUF"),
])
def test_gguf_reports_invalid_files(name, content, error, tmp_path, capsys):
    path = tmp_path / name
    path.write_bytes(content)
    with pytest.raises(SystemExit) as exc:
        cli.main(["gguf", str(path), "--json"])
    assert exc.value.code == 2
    report = capsys.readouterr()
    assert error in report.err
    assert report.out == ""


def test_split_gguf_estimates_all_shards_once(tmp_path, monkeypatch, capsys):
    import struct

    monkeypatch.setattr(cli, "detect_hardware", mock_machine)
    first, second = (tmp_path / f"model-{idx:05d}-of-00002.gguf" for idx in (1, 2))
    header = b"GGUF" + struct.pack("<IQQ", 3, 1, 0)
    first.write_bytes(header.ljust(1024, b"\x00"))
    second.write_bytes(header.ljust(4096, b"\x00"))
    assert cli.main(["gguf", str(second), str(first), "--json"]) == 0
    report = json.loads(capsys.readouterr().out)
    model, = report["gguf_files"]
    result, = report["results"]
    assert model["size_bytes"] == 5120
    assert model["shard_count"] == 2
    assert [shard["path"] for shard in model["shards"]] == [str(first), str(second)]
    assert result["download_gb"] == 5120 / 10**9

    assert cli.main(["gguf", str(second), "--target", "gpu", "--json"]) == 0
    gpu_report = json.loads(capsys.readouterr().out)
    assert gpu_report["target"] == "gpu"
    assert gpu_report["gguf_files"][0]["size_bytes"] == 5120
    assert gpu_report["results"][0]["status"] == "unlikely"

    second.unlink()
    with pytest.raises(SystemExit) as exc:
        cli.main(["gguf", str(first), "--json"])
    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert second.name in captured.err
    assert not captured.out


def test_gpu_shortlist_excludes_cpu_fallbacks(monkeypatch, capsys):
    monkeypatch.setattr(cli, "detect_hardware", mock_machine)
    args = ["recommend", "--fits-only", "--ram-gb", "8", "--vram-gb", "2", "--json"]
    assert cli.main(args) == 0
    automatic = json.loads(capsys.readouterr().out)
    assert "target" not in automatic
    assert any(row["status"] == "likely_cpu" for row in automatic["results"])

    assert cli.main(args + ["--target", "gpu"]) == 0
    gpu_only = json.loads(capsys.readouterr().out)
    assert gpu_only["target"] == "gpu"
    assert gpu_only["results"] == [
        row for row in automatic["results"] if row["status"] == "likely_gpu"
    ]
    assert gpu_only["results"]


@pytest.mark.parametrize("args", [["check", "qwen3:4b"], ["estimate", "2"]])
def test_single_model_commands_honor_target(args, monkeypatch, capsys):
    monkeypatch.setattr(cli, "detect_hardware", mock_machine)
    assert cli.main(args + ["--target", "cpu", "--vram-gb", "8"]) == 0
    output = capsys.readouterr().out
    assert "Fit target: CPU" in output
    assert "likely_cpu" in output
