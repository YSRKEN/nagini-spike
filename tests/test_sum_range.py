"""範囲の和の仕様を先に固定し、実行と静的検証で確かめる。"""

import subprocess
import sys
from pathlib import Path

import pytest

import scripts.check as check
from examples.sum_range import sum_range

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "sum_range.py"


@pytest.mark.parametrize("n", [0, 1, 2, 5, 10, 100])
def test_sum_matches_python(n: int) -> None:
    """空の範囲、境界、複数回の繰り返しを組み込みのsumと照合する。"""
    assert sum_range(n) == sum(range(n))


def test_negative_input_is_rejected() -> None:
    """検証上の前提だけに頼らず、通常の実行でも負数を拒否する。"""
    with pytest.raises(AssertionError):
        sum_range(-1)


def test_sum_verifies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """選んだ入力の実行に加え、Naginiで最後の仕様を検証する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    returncode, output = check.run(["-m", "nagini_translation.main", str(SOURCE)], "sum_range")
    assert check.accepted(returncode, output), output


@pytest.mark.parametrize("mutation", ["wrong_sum", "missing_invariant"])
def test_sum_rejects_mutation(
    mutation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """誤計算と、正しい計算だが証明用の情報が足りない場合を区別する。"""
    source = SOURCE.read_text(encoding="utf-8")
    if mutation == "wrong_sum":
        original = "total += i"
        replacement = "total += i + 1"
        diagnostic = (
            "Loop invariant might not be preserved. "
            "Assertion 2 * total == i * (i - 1) might not hold."
        )
    else:
        original = "        Invariant(2 * total == i * (i - 1))\n"
        replacement = ""
        diagnostic = "Assertion 2 * total == n * (n - 1) might not hold."
    assert source.count(original) == 1
    changed = source.replace(original, replacement)
    assert changed != source
    path = tmp_path / (mutation + ".py")
    path.write_text(changed, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    returncode, output = check.run(["-m", "nagini_translation.main", str(path)], mutation)
    assert returncode == 1, output
    assert "Verification failed" in output, output
    assert diagnostic in output, output

    probe = "import runpy,sys; assert runpy.run_path(sys.argv[1])['sum_range'](10) == 45"
    process = subprocess.run(
        [sys.executable, "-c", probe, str(path)], capture_output=True, text=True, timeout=10
    )
    if mutation == "missing_invariant":
        assert process.returncode == 0, process.stdout + process.stderr
    else:
        assert process.returncode != 0
        assert "AssertionError" in process.stderr
