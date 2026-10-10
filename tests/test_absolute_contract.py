"""仕様を固定して実装し、契約が呼び出し側に届くことを確かめる。"""

import subprocess
import sys
from pathlib import Path
from typing import Literal

import pytest

import scripts.check as check
import scripts.extract_absolute as extractor
from scripts.verification_cases import (
    ExpectedVerification,
    Mutation,
    Specification,
    VerificationCase,
    verify_case,
)

SPECIFICATION = Specification(
    "absoluteの結果が非負かつxまたは-x、callerで非負性を利用する",
    "既知のAST宣言だけを除去したコピーでabsとcallerを照合する",
)

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "absolute_contract.py"


def test_contract_verifies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """実装の契約と、それを利用する呼び出し側の両方が通る。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    monkeypatch.setattr(extractor, "RESULTS", tmp_path)
    assert extractor.main() == 0
    path = tmp_path / "absolute_runtime.py"
    probe = (
        "import runpy, sys; m = runpy.run_path(sys.argv[1]); "
        "assert m['absolute'](-1) == 1; m['caller'](-1)"
    )
    process = subprocess.run(
        [sys.executable, "-c", probe, str(path)], capture_output=True, text=True, timeout=10
    )
    assert process.returncode == 0, process.stdout + process.stderr


@pytest.mark.parametrize("mutation", ["wrong_implementation", "missing_contract"])
def test_contract_rejects_mutation(
    mutation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """実装の誤りと、呼び出し側に保証が届かない場合を区別して検出する。"""
    source = SOURCE.read_text(encoding="utf-8")
    if mutation == "wrong_implementation":
        original = "return -x"
        replacement = "return x"
        diagnostic = (
            "Postcondition of absolute might not hold. Assertion ResultT(int) >= 0 might not hold."
        )
    else:
        original = "    Ensures(ResultT(int) >= 0)\n"
        replacement = ""
        diagnostic = "Assertion result >= 0 might not hold."
    change = Mutation(original, replacement)
    broken = change.apply(source)
    assert broken != source
    path = tmp_path / (mutation + ".py")
    path.write_text(broken, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    category: Literal["verified", "proof_failure"] = "proof_failure"
    required_diagnostics: list[str] = []
    required_diagnostics.append(diagnostic)
    case = VerificationCase(
        mutation, SPECIFICATION, ExpectedVerification(category, tuple(required_diagnostics)), change
    )
    verify_case(case, path)
