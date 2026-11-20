from types import SimpleNamespace

from modelfit import hardware


def test_nvidia_probe_selects_gpu_with_most_free_memory(monkeypatch):
    def fake_run(*args, **kwargs):
        return SimpleNamespace(
            returncode=0,
            stdout="GPU Small, 8192, 2000\nGPU Big, 24576, 16000\n",
        )
    monkeypatch.setattr(hardware.subprocess, "run", fake_run)
    assert hardware.detect_nvidia_gpu() == ("GPU Big", 24.0, 15.625)


def test_nvidia_probe_falls_back_when_unavailable(monkeypatch):
    def missing(*args, **kwargs):
        raise FileNotFoundError("nvidia-smi")
    monkeypatch.setattr(hardware.subprocess, "run", missing)
    assert hardware.detect_nvidia_gpu() is None


def test_nvidia_probe_ignores_corrupted_rows(monkeypatch):
    monkeypatch.setattr(
        hardware.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="bad row\nGPU, 4096, 2048\n"),
    )
    assert hardware.detect_nvidia_gpu() == ("GPU", 4.0, 2.0)


def test_detect_hardware_with_mocked_memory(monkeypatch):
    monkeypatch.setattr(hardware, "detect_nvidia_gpu", lambda: None)
    monkeypatch.setattr(
        hardware.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(total=16 * hardware.GIB, available=8 * hardware.GIB),
    )
    result = hardware.detect_hardware()
    assert result.available_ram_gib == 8
    assert result.total_ram_gib == 16
    assert result.free_vram_gib is None
