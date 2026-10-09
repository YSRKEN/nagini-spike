"""仕様を固定して実装し、契約が呼び出し側に届くことを確かめる。"""

from pathlib import Path

import pytest

import scripts.check as check

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "absolute_contract.py"


def test_contract_verifies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """実装の契約と、それを利用する呼び出し側の両方が通る。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    returncode, output = check.run(["-m", "nagini_translation.main", str(SOURCE)], "contract")
    assert check.accepted(returncode, output), output


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
    assert source.count(original) == 1
    broken = source.replace(original, replacement)
    assert broken != source
    path = tmp_path / (mutation + ".py")
    path.write_text(broken, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    returncode, output = check.run(["-m", "nagini_translation.main", str(path)], mutation)
    assert returncode == 1, output
    assert "Verification failed" in output, output
    assert diagnostic in output, output
