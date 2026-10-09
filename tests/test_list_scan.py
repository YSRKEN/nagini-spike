"""リスト走査の実行結果と、非負性の静的仕様を区別する。"""

import subprocess
import sys
from pathlib import Path

import pytest

import scripts.check as check
from examples.list_scan import sum_nonnegative

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "list_scan.py"


@pytest.mark.parametrize("values", [[], [0], [7], [1, 2, 3], [0, 7, 0], [10**100, 1]])
def test_scan_matches_sum(values: list[int]) -> None:
    """合計値と入力が変わらないことを具体例で検査する。"""
    before = values.copy()
    assert sum_nonnegative(values) == sum(values)
    assert values == before


@pytest.mark.parametrize("values", [[-1], [0, -3]])
def test_negative_element_fails_at_runtime(values: list[int]) -> None:
    """検証の前提に反する入力を通常実行でも拒否する。"""
    with pytest.raises(AssertionError):
        sum_nonnegative(values)


def test_scan_verifies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """権限と途中の非負性を保つループの最後の条件を検証する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    code, output = check.run(["-m", "nagini_translation.main", str(SOURCE)], "list_scan")
    assert check.accepted(code, output), output


@pytest.mark.parametrize("mutation", ["subtract", "missing_permission", "skip_sum"])
def test_scan_boundaries(mutation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """計算の誤り・証明情報の不足・仕様が縛らない誤りを比較する。"""
    source = SOURCE.read_text(encoding="utf-8")
    if mutation == "missing_permission":
        original = (
            "        Invariant(Acc(list_pred(values), 1 / 2))  "
            "# pyright: ignore[reportArgumentType]\n"
        )
        replacement = ""
    else:
        original = "        total += values[i]\n"
        replacement = "        total -= values[i]\n" if mutation == "subtract" else ""
    assert source.count(original) == 1
    path = tmp_path / (mutation + ".py")
    path.write_text(source.replace(original, replacement), encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    code, output = check.run(["-m", "nagini_translation.main", str(path)], mutation)
    if mutation == "skip_sum":
        assert check.accepted(code, output), output
    else:
        assert code == 1, output
        assert "Verification failed" in output, output
        if mutation == "subtract":
            assert "Loop invariant might not be preserved." in output, output
            assert "Assertion total >= 0 might not hold." in output, output
        else:
            assert "insufficient permission" in output, output
    probe = "import runpy,sys; assert runpy.run_path(sys.argv[1])['sum_nonnegative']([1,2,3]) == 6"
    process = subprocess.run(
        [sys.executable, "-c", probe, str(path)], capture_output=True, text=True, timeout=10
    )
    if mutation == "missing_permission":
        assert process.returncode == 0, process.stdout + process.stderr
    else:
        assert process.returncode != 0
        assert "AssertionError" in process.stderr
