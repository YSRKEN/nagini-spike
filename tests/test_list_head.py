"""リストの先頭を読む仕様を、実行と静的検証で確かめる。"""

import subprocess
import sys
from pathlib import Path

import pytest

import scripts.check as check
from examples.list_head import first_or_zero

SOURCE = Path(__file__).resolve().parents[1] / "examples" / "list_head.py"


@pytest.mark.parametrize("values", [[], [0], [7], [-3], [7, 99], [-(10**100), 1]])
def test_first_matches_python(values: list[int]) -> None:
    """空、単一要素、複数要素を照合し、入力が変わらないことも確かめる。"""
    before = values.copy()
    assert first_or_zero(values) == (values[0] if values else 0)
    assert values == before


def test_first_verifies(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """添字の安全性と、最後の二つの仕様をNaginiで検証する。"""
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    returncode, output = check.run(["-m", "nagini_translation.main", str(SOURCE)], "list_head")
    assert check.accepted(returncode, output), output


@pytest.mark.parametrize("mutation", ["bad_index", "missing_permission", "write_attempt"])
def test_first_rejects_mutation(
    mutation: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """添字の誤り、権限不足、読み取り専用の権限での書き込みを区別する。"""
    source = SOURCE.read_text(encoding="utf-8")
    if mutation == "missing_permission":
        original = "Requires(Acc(list_pred(values), 1 / 2))"
        replacement = "pass"
        diagnostic = (
            "The precondition of function len might not hold. "
            "There might be insufficient permission."
        )
    elif mutation == "write_attempt":
        original = "result = values[0]"
        replacement = "values[0] = 0\n        result = values[0]"
        diagnostic = (
            "The precondition of values[0] = 0 might not hold. "
            "There might be insufficient permission."
        )
    else:
        original = "result = values[0]"
        replacement = "result = values[1]"
        diagnostic = "The precondition of values[1] might not hold."
    assert source.count(original) == 1
    changed = source.replace(original, replacement)
    assert changed != source
    path = tmp_path / (mutation + ".py")
    path.write_text(changed, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    returncode, output = check.run(["-m", "nagini_translation.main", str(path)], mutation)
    assert returncode == 1, output
    assert "Verification failed" in output, output
    assert diagnostic in output, output

    probe = (
        "import runpy,sys; values = [7]; "
        "assert runpy.run_path(sys.argv[1])['first_or_zero'](values) == 7; "
        "assert values == [7]"
    )
    process = subprocess.run(
        [sys.executable, "-c", probe, str(path)], capture_output=True, text=True, timeout=10
    )
    if mutation == "missing_permission":
        assert process.returncode == 0, process.stdout + process.stderr
    else:
        assert process.returncode != 0
        expected = "IndexError" if mutation == "bad_index" else "AssertionError"
        assert expected in process.stderr
