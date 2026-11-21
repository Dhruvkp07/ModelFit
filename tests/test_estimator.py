import pytest

from modelfit.estimator import assess, estimated_memory_gib, recommend
from modelfit.hardware import Hardware


def machine(ram=10, vram=None):
    return Hardware("TestOS", "Test CPU", 8, 16, ram, "GPU" if vram is not None else None, vram, vram)


MODEL = {"name": "test:small", "download_gb": 2.0, "source": "https://example.org"}


def test_gpu_fit():
    result = assess(MODEL, machine(ram=5, vram=8))
    assert result.status == "likely_gpu"
    assert result.estimated_memory_gib == 3.15


def test_cpu_fallback_when_vram_insufficient():
    assert assess(MODEL, machine(ram=8, vram=1)).status == "likely_cpu"


def test_insufficient_memory():
    assert assess(MODEL, machine(ram=2, vram=1)).status == "unlikely"


def test_one_gpu_without_enough_host_ram_not_gpu_fit():
    result = assess(MODEL, machine(ram=0.5, vram=8))
    assert result.status == "unlikely"
    assert "host RAM" in result.reason


def test_unknown_gpu_is_not_reported_as_insufficient_vram():
    result = assess(MODEL, machine(ram=2))
    assert "not detected" in result.reason


@pytest.mark.parametrize("size", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_model_size(size):
    with pytest.raises(ValueError):
        estimated_memory_gib(size)


def test_invalid_model_size():
    with pytest.raises(ValueError):
        estimated_memory_gib(-1)


def test_recommend_sorted_by_fit_and_size():
    models = [
        {"name": "large", "download_gb": 10, "source": "a"},
        {"name": "small", "download_gb": 1, "source": "b"},
    ]
    output = recommend(models, machine(ram=4, vram=3))
    assert [item.name for item in output] == ["small", "large"]
    assert [item.status for item in output] == ["likely_gpu", "unlikely"]
