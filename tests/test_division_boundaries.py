"""整数の商と余りの仕様を境界の実行と静的検証で照合する。"""

import subprocess
import sys
from pathlib import Path

import pytest

import scripts.check as check
from examples.division_boundaries import quotient_remainder

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "division_boundaries.py"


@pytest.mark.parametrize(
    "numerator,divisor",
    [(0, 1), (0, 3), (7, 1), (7, 3), (-7, 3), (-1, 1), (10**100, 3), (-(10**100), 7)],
)
def test_division_matches_python(numerator: int, divisor: int) -> None:
    """ゼロ、除数1、負の入力、大きな整数を組み込みのdivmodと照合する。"""
    assert quotient_remainder(numerator, divisor) == divmod(numerator, divisor)


@pytest.mark.parametrize("divisor", [0, -3])
def test_invalid_divisor_fails_early(divisor: int) -> None:
    """通常実行では演算する前に対象外の除数を拒否する。"""
    with pytest.raises(AssertionError):
        quotient_remainder(7, divisor)


def test_division_verifies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """再構成の等式と余りの範囲をNaginiで検証する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    code, output = check.run(["-m", "nagini_translation.main", str(SOURCE)], "division")
    assert check.accepted(code, output), output


@pytest.mark.parametrize("mutation", ["wrong_quotient", "wrong_remainder", "no_guard"])
def test_division_rejects_target_failure(
    mutation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """商・余りの誤りと、除数の安全条件の不足を区別する。"""
    source = SOURCE.read_text(encoding="utf-8")
    changes = {
        "wrong_quotient": (
            "quotient = numerator // divisor",
            "quotient = numerator // divisor + 1",
        ),
        "wrong_remainder": (
            "remainder = numerator % divisor",
            "remainder = numerator % divisor + divisor",
        ),
        "no_guard": ("    Requires(divisor > 0)\n    assert divisor > 0\n", ""),
    }
    original, replacement = changes[mutation]
    assert source.count(original) == 1
    path = tmp_path / (mutation + ".py")
    path.write_text(source.replace(original, replacement), encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    code, output = check.run(["-m", "nagini_translation.main", str(path)], mutation)
    assert code == 1, output
    assert "Verification failed" in output, output
    if mutation == "no_guard":
        assert "The precondition of numerator // divisor might not hold." in output, output
    else:
        assert "Assertion numerator == quotient * divisor + remainder might not hold." in output, (
            output
        )
    divisor = 0 if mutation == "no_guard" else 3
    probe = (
        "import runpy,sys; "
        f"assert runpy.run_path(sys.argv[1])['quotient_remainder'](-7,{divisor}) == (-3,2)"
    )
    process = subprocess.run(
        [sys.executable, "-c", probe, str(path)], capture_output=True, text=True, timeout=10
    )
    assert process.returncode != 0
    expected = "ZeroDivisionError" if mutation == "no_guard" else "AssertionError"
    assert expected in process.stderr
