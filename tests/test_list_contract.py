"""仕様を実装と呼び出し側の間の契約として利用する。"""

import subprocess
import sys
from pathlib import Path
from typing import Literal

import pytest

import scripts.check as check
from examples.list_contract import replace_head
from scripts.verification_cases import (
    ExpectedVerification,
    Mutation,
    Specification,
    VerificationCase,
    verify_case,
)

SPECIFICATION = Specification(
    "非空リストの先頭が指定値、長さと全権限をcallerへ返す",
    "既知宣言を除くコピーで先頭更新とcallerの再更新、後続値を照合する",
)

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "list_contract.py"


def test_contract_needs_runtime_preparation() -> None:
    """契約宣言付きの直接実行を動作確認と取り違えない。"""
    with pytest.raises(NotImplementedError, match="overloaded function"):
        replace_head([7], 9)


def test_contract_verifies_and_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """同じソースを検証し、既知の事後条件だけを除いたコピーで具体例を実行する。"""
    source = SOURCE.read_text(encoding="utf-8")
    verified = tmp_path / "verified.py"
    verified.write_text(source, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    case = VerificationCase("list_contract", SPECIFICATION, ExpectedVerification("verified"))
    verify_case(case, verified)
    assert verified.read_text(encoding="utf-8") == source
    declarations = [
        "    Ensures(Acc(list_pred(values)))\n",
        "    Ensures(len(values) == Old(len(values)))\n",
        "    Ensures(values[0] == value)\n",
    ]
    runtime = source
    for declaration in declarations:
        assert runtime.count(declaration) == 1
        runtime = runtime.replace(declaration, "\n")
    assert runtime.count("Ensures(") == 0
    path = tmp_path / "runtime.py"
    path.write_text(runtime, encoding="utf-8")
    probe = """
import runpy, sys
module = runpy.run_path(sys.argv[1])
for values in ([7], [7, 99], [-3, 10**100]):
    before = values.copy()
    module['replace_head'](values, 9)
    assert values == [9, *before[1:]]
    module['caller'](values, -17)
    assert values == [-16, *before[1:]]
"""
    process = subprocess.run(
        [sys.executable, "-c", probe, str(path)], capture_output=True, text=True, timeout=10
    )
    assert process.returncode == 0, process.stdout + process.stderr


@pytest.mark.parametrize("mutation", ["wrong_value", "read_only_return", "no_value"])
def test_contract_rejects_target_failure(
    mutation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """実装の誤りと呼び出し側へ返す契約の不足を区別する。"""
    source = SOURCE.read_text(encoding="utf-8")
    changes = {
        "wrong_value": ("    values[0] = value\n", "    values[0] = value + 1\n"),
        "read_only_return": (
            "    Ensures(Acc(list_pred(values)))\n",
            "    Ensures(Acc(list_pred(values), 1 / 2))\n",
        ),
        "no_value": ("    Ensures(values[0] == value)\n", ""),
    }
    original, replacement = changes[mutation]
    change = Mutation(original, replacement)
    path = tmp_path / (mutation + ".py")
    path.write_text(change.apply(source), encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    category: Literal["verified", "proof_failure"] = "proof_failure"
    required_diagnostics: list[str] = []
    if mutation == "wrong_value":
        required_diagnostics.append("Postcondition of replace_head might not hold.")
        required_diagnostics.append("Assertion values[0] == value might not hold.")
    elif mutation == "read_only_return":
        required_diagnostics.append("The precondition of values[0] = value + 1 might not hold.")
        required_diagnostics.append("insufficient permission")
    else:
        required_diagnostics.append("Assertion values[0] == value might not hold.")
    case = VerificationCase(
        mutation, SPECIFICATION, ExpectedVerification(category, tuple(required_diagnostics)), change
    )
    verify_case(case, path)
