"""整数の商と余りの仕様を境界の実行と静的検証で照合する。"""

import subprocess
import sys
from pathlib import Path
from typing import Literal

import pytest

import scripts.check as check
from examples.division_boundaries import quotient_remainder
from scripts.verification_cases import (
    ExpectedVerification,
    Mutation,
    Specification,
    VerificationCase,
    verify_case,
)

SPECIFICATION = Specification(
    "除数が正の下で商と余りの再構成等式、余りが0以上で除数未満",
    "divmodと照合し、対象外除数はAssertionError、ガード除去時0除算はZeroDivisionError",
)

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
    case = VerificationCase("division", SPECIFICATION, ExpectedVerification("verified"))
    verify_case(case, SOURCE)


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
    change = Mutation(original, replacement)
    path = tmp_path / (mutation + ".py")
    path.write_text(change.apply(source), encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    category: Literal["verified", "proof_failure"] = "proof_failure"
    required_diagnostics: list[str] = []
    if mutation == "no_guard":
        required_diagnostics.append("The precondition of numerator // divisor might not hold.")
    else:
        required_diagnostics.append(
            "Assertion numerator == quotient * divisor + remainder might not hold."
        )
    case = VerificationCase(
        mutation, SPECIFICATION, ExpectedVerification(category, tuple(required_diagnostics)), change
    )
    verify_case(case, path)
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
