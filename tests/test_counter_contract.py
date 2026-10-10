"""クラスの属性とメソッドの保証を実行と静的検証で確かめる。"""

import subprocess
import sys
from pathlib import Path
from typing import Literal

import pytest

import scripts.check as check
from examples.counter_contract import Counter
from scripts.verification_cases import (
    ExpectedVerification,
    Mutation,
    Specification,
    VerificationCase,
    verify_case,
)

SPECIFICATION = Specification(
    "初期値とincrement前後の値、属性の書き込み権限をcallerへ返す",
    "直接宣言はNotImplementedError、既知宣言を除くコピーで初期化と2回更新を照合する",
)

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "counter_contract.py"


def test_direct_construction_needs_preparation() -> None:
    """配布物の事後条件宣言の直接実行を検証成功と取り違えない。"""
    with pytest.raises(NotImplementedError, match="overloaded function"):
        Counter(0)


def test_counter_verifies_and_runs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """同じソースを検証した後、既知の契約を除いたコピーで具体例を実行する。"""
    source = SOURCE.read_text(encoding="utf-8")
    verified = tmp_path / "verified.py"
    verified.write_text(source, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    case = VerificationCase("counter", SPECIFICATION, ExpectedVerification("verified"))
    verify_case(case, verified)
    assert verified.read_text(encoding="utf-8") == source
    declarations = {
        "        Ensures(Acc(self.value))\n": 2,
        "        Ensures(self.value == initial)\n": 1,
        "        Ensures(self.value == Old(self.value) + 1)\n": 1,
    }
    runtime = source
    for declaration, count in declarations.items():
        assert runtime.count(declaration) == count
        runtime = runtime.replace(declaration, "\n")
    assert "Ensures(" not in runtime
    path = tmp_path / "runtime.py"
    path.write_text(runtime, encoding="utf-8")
    probe = """
import runpy, sys
module = runpy.run_path(sys.argv[1])
for initial in (0, 7, -3, 10**100, -10**100):
    counter = module['Counter'](initial)
    assert counter.value == initial
    counter.increment()
    assert counter.value == initial + 1
    counter.increment()
    assert counter.value == initial + 2
    module['caller'](initial)
"""
    process = subprocess.run(
        [sys.executable, "-c", probe, str(path)], capture_output=True, text=True, timeout=10
    )
    assert process.returncode == 0, process.stdout + process.stderr


@pytest.mark.parametrize("mutation", ["wrong_initial", "wrong_increment", "no_value", "read_only"])
def test_counter_rejects_target_failure(
    mutation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """初期化・更新の誤りと、呼び出し側の値・権限の不足を区別する。"""
    source = SOURCE.read_text(encoding="utf-8")
    changes = {
        "wrong_initial": ("self.value: int = initial", "self.value: int = initial + 1"),
        "wrong_increment": ("self.value += 1", "self.value += 2"),
        "no_value": ("        Ensures(self.value == Old(self.value) + 1)\n", ""),
        "read_only": (
            "        Requires(Acc(self.value))\n        Ensures(Acc(self.value))",
            "        Requires(Acc(self.value))\n        Ensures(Acc(self.value, 1 / 2))",
        ),
    }
    original, replacement = changes[mutation]
    change = Mutation(original, replacement)
    path = tmp_path / (mutation + ".py")
    path.write_text(change.apply(source), encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    category: Literal["verified", "proof_failure"] = "proof_failure"
    required_diagnostics: list[str] = []
    if mutation in ("wrong_initial", "wrong_increment"):
        required_diagnostics.append("Postcondition of")
        diagnostic = (
            "Assertion self.value == initial might not hold."
            if mutation == "wrong_initial"
            else "Assertion self.value == Old(self.value) + 1 might not hold."
        )
        required_diagnostics.append(diagnostic)
    elif mutation == "no_value":
        required_diagnostics.append("Assertion counter.value == initial + 1 might not hold.")
    else:
        required_diagnostics.append("insufficient permission")
        required_diagnostics.append("increment")
    case = VerificationCase(
        mutation, SPECIFICATION, ExpectedVerification(category, tuple(required_diagnostics)), change
    )
    verify_case(case, path)
