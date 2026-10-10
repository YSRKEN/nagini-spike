"""先頭以外の値の維持を静的仕様で保証できるか検査する。"""

from pathlib import Path
from typing import Literal

import pytest

import scripts.check as check
from examples.list_frame import replace_first_preserving_tail
from scripts.verification_cases import (
    ExpectedVerification,
    Mutation,
    Specification,
    VerificationCase,
    verify_case,
)

SPECIFICATION = Specification(
    "全書き込み権限の下で先頭だけ更新し、長さと全後続値を維持する",
    "空と非空のリストで先頭以外と長さの維持を照合する",
)

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "list_frame.py"


@pytest.mark.parametrize("values", [[], [7], [7, 99], [7, -3, 10**100]])
def test_preserves_tail_at_runtime(values: list[int]) -> None:
    """通常実行でも先頭以外の値と長さが維持される。"""
    before = values.copy()
    replace_first_preserving_tail(values, 9)
    assert values == ([9, *before[1:]] if before else [])


def test_frame_verifies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """実装が変更範囲の仕様を満たすことを静的検証する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    case = VerificationCase("list_frame", SPECIFICATION, ExpectedVerification("verified"))
    verify_case(case, SOURCE)


def test_extra_change_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """先頭以外を変更する実装は同じ仕様の下で拒否される。"""
    source = SOURCE.read_text(encoding="utf-8")
    original = "values[0] = value"
    replacement = "values[0] = value\n        if len(values) > 1:\n            values[1] = 0"
    change = Mutation(original, replacement)
    changed = change.apply(source)
    path = tmp_path / "extra_change.py"
    path.write_text(changed, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    category: Literal["verified", "proof_failure"] = "proof_failure"
    required_diagnostics: list[str] = []
    required_diagnostics.append(
        "Assertion Forall(int, lambda i: Implies(1 <= i and i < len(values), "
        "values[i] == before[i])) might not hold."
    )
    case = VerificationCase(
        "extra_change",
        SPECIFICATION,
        ExpectedVerification(category, tuple(required_diagnostics)),
        change,
    )
    verify_case(case, path)
