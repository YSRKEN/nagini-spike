"""書き込みの仕様を先に固定し、実行と静的検証で確かめる。"""

import subprocess
import sys
from pathlib import Path
from typing import Literal

import pytest

import scripts.check as check
from examples.list_write import replace_first
from scripts.verification_cases import (
    ExpectedVerification,
    Mutation,
    Specification,
    VerificationCase,
    verify_case,
)

SPECIFICATION = Specification(
    "全書き込み権限の下で長さ維持と空または先頭が指定値、後続値の維持は仕様にない",
    "先頭以外も維持される期待値を照合する。extra_changeは静的に通るが実行照合で失敗する",
)

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "list_write.py"


@pytest.mark.parametrize(
    "values,value",
    [
        ([], 7),
        ([7], 9),
        ([0], 0),
        ([-3], 0),
        ([7, 99], -17),
        ([7, 7], 5),
        ([10**100, 1], -(10**100)),
    ],
)
def test_replacement_matches_python(values: list[int], value: int) -> None:
    """空、単一、複数の要素について、先頭以外と長さが変わらないことも確認する。"""
    before = values.copy()
    result = replace_first(values, value)
    expected = [value, *before[1:]] if before else []
    assert result is None
    assert values == expected


def test_replacement_verifies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """添字の安全性、長さの維持、先頭の値をNaginiで検証する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    case = VerificationCase("list_write", SPECIFICATION, ExpectedVerification("verified"))
    verify_case(case, SOURCE)


@pytest.mark.parametrize("mutation", ["wrong_value", "read_only", "extra_change"])
def test_replacement_boundaries(
    mutation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """権限・指定値の違反と、静的仕様に含めていない変更を区別する。"""
    source = SOURCE.read_text(encoding="utf-8")
    if mutation == "read_only":
        original = "Acc(list_pred(values))"
        replacement = "Acc(list_pred(values), 1 / 2)"
        diagnostic = (
            "The precondition of values[0] = value might not hold. "
            "There might be insufficient permission."
        )
    elif mutation == "extra_change":
        original = "values[0] = value"
        replacement = "values[0] = value\n        if len(values) > 1:\n            values[1] = 0"
        diagnostic = ""
    else:
        original = "values[0] = value"
        replacement = "values[0] = value + 1"
        diagnostic = "Assertion len(values) == 0 or values[0] == value might not hold."
    change = Mutation(original, replacement)
    changed = change.apply(source)
    assert changed != source
    path = tmp_path / (mutation + ".py")
    path.write_text(changed, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    category: Literal["verified", "proof_failure"] = "proof_failure"
    required_diagnostics: list[str] = []
    if mutation == "extra_change":
        category = "verified"
    else:
        required_diagnostics.append(diagnostic)
    case = VerificationCase(
        mutation, SPECIFICATION, ExpectedVerification(category, tuple(required_diagnostics)), change
    )
    verify_case(case, path)

    probe = (
        "import runpy,sys; values = [7, 99]; "
        "runpy.run_path(sys.argv[1])['replace_first'](values, 9); "
        "assert values == [9, 99]"
    )
    process = subprocess.run(
        [sys.executable, "-c", probe, str(path)], capture_output=True, text=True, timeout=10
    )
    if mutation == "read_only":
        assert process.returncode == 0, process.stdout + process.stderr
    else:
        assert process.returncode != 0
        assert "AssertionError" in process.stderr
