"""リスト走査の実行結果と、非負性の静的仕様を区別する。"""

import subprocess
import sys
from pathlib import Path
from typing import Literal

import pytest

import scripts.check as check
from examples.list_scan import sum_nonnegative
from scripts.verification_cases import (
    ExpectedVerification,
    Mutation,
    Specification,
    VerificationCase,
    verify_case,
)

SPECIFICATION = Specification(
    "非負要素と読取り権限の下で走査途中と結果の非負性、合計等式は仕様にない",
    "sumと入力不変、負数拒否を照合する。skip_sumは静的に通るが実行照合で失敗する",
)

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
    case = VerificationCase("list_scan", SPECIFICATION, ExpectedVerification("verified"))
    verify_case(case, SOURCE)


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
    change = Mutation(original, replacement)
    path = tmp_path / (mutation + ".py")
    path.write_text(change.apply(source), encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    category: Literal["verified", "proof_failure"] = "proof_failure"
    required_diagnostics: list[str] = []
    if mutation == "skip_sum":
        category = "verified"
    elif mutation == "subtract":
        required_diagnostics.append("Loop invariant might not be preserved.")
        required_diagnostics.append("Assertion total >= 0 might not hold.")
    else:
        required_diagnostics.append("insufficient permission")
    case = VerificationCase(
        mutation, SPECIFICATION, ExpectedVerification(category, tuple(required_diagnostics)), change
    )
    verify_case(case, path)
    probe = "import runpy,sys; assert runpy.run_path(sys.argv[1])['sum_nonnegative']([1,2,3]) == 6"
    process = subprocess.run(
        [sys.executable, "-c", probe, str(path)], capture_output=True, text=True, timeout=10
    )
    if mutation == "missing_permission":
        assert process.returncode == 0, process.stdout + process.stderr
    else:
        assert process.returncode != 0
        assert "AssertionError" in process.stderr
