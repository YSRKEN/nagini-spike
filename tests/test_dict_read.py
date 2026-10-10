"""辞書のキーの有無、参照の安全性、権限を実行と証明で比較する。"""

import subprocess
import sys
from pathlib import Path
from typing import Literal

import pytest

import scripts.check as check
from examples.dict_read import lookup_or_zero
from scripts.verification_cases import (
    ExpectedVerification,
    Mutation,
    Specification,
    VerificationCase,
    verify_case,
)

SPECIFICATION = Specification(
    "読取り権限の下でキー存在時の値、不在時0、キー参照の安全性",
    "dict.getと入力不変を照合する。別キーはKeyError、代入はAssertionError",
)

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "dict_read.py"


@pytest.mark.parametrize(
    "values,key",
    [({}, 1), ({1: 7}, 1), ({1: 7}, 2), ({0: 0}, 0), ({-3: -9}, -3), ({1: 10**100, 2: 99}, 1)],
)
def test_lookup_matches_dict(values: dict[int, int], key: int) -> None:
    """空、キーの有無、ゼロ、負数、大きな整数の具体例を確認する。"""
    before = values.copy()
    assert lookup_or_zero(values, key) == values.get(key, 0)
    assert values == before


def test_lookup_verifies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """キー存在時の値と不在時の0、および参照の安全性を検証する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    case = VerificationCase("dict_read", SPECIFICATION, ExpectedVerification("verified"))
    verify_case(case, SOURCE)


@pytest.mark.parametrize("mutation", ["bad_key", "missing_permission", "write_attempt"])
def test_lookup_rejects_target_failure(
    mutation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """別キーの参照、権限不足、読み取り権限での代入を区別する。"""
    source = SOURCE.read_text(encoding="utf-8")
    if mutation == "missing_permission":
        original = "Requires(Acc(dict_pred(values), 1 / 2))"
        replacement = "pass"
    else:
        original = "result = values[key]"
        replacement = (
            "result = values[key + 1]"
            if mutation == "bad_key"
            else "values[key] = 0\n        result = values[key]"
        )
    change = Mutation(original, replacement)
    path = tmp_path / (mutation + ".py")
    path.write_text(change.apply(source), encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    category: Literal["verified", "proof_failure"] = "proof_failure"
    required_diagnostics: list[str] = []
    if mutation == "bad_key":
        required_diagnostics.append("The precondition of values[key + 1] might not hold.")
    else:
        required_diagnostics.append("insufficient permission")
        if mutation == "write_attempt":
            required_diagnostics.append("The precondition of values[key] = 0 might not hold.")
    case = VerificationCase(
        mutation, SPECIFICATION, ExpectedVerification(category, tuple(required_diagnostics)), change
    )
    verify_case(case, path)
    probe = (
        "import runpy,sys; values = {1: 7}; "
        "assert runpy.run_path(sys.argv[1])['lookup_or_zero'](values, 1) == 7; "
        "assert values == {1: 7}"
    )
    process = subprocess.run(
        [sys.executable, "-c", probe, str(path)], capture_output=True, text=True, timeout=10
    )
    if mutation == "missing_permission":
        assert process.returncode == 0, process.stdout + process.stderr
    else:
        assert process.returncode != 0
        expected = "KeyError" if mutation == "bad_key" else "AssertionError"
        assert expected in process.stderr
