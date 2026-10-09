"""先頭以外の値の維持を静的仕様で保証できるか検査する。"""

from pathlib import Path

import pytest

import scripts.check as check
from examples.list_frame import replace_first_preserving_tail

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
    code, output = check.run(["-m", "nagini_translation.main", str(SOURCE)], "list_frame")
    assert check.accepted(code, output), output


def test_extra_change_is_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """先頭以外を変更する実装は同じ仕様の下で拒否される。"""
    source = SOURCE.read_text(encoding="utf-8")
    original = "values[0] = value"
    assert source.count(original) == 1
    changed = source.replace(
        original, "values[0] = value\n        if len(values) > 1:\n            values[1] = 0"
    )
    path = tmp_path / "extra_change.py"
    path.write_text(changed, encoding="utf-8")
    monkeypatch.setattr(check, "RESULTS", tmp_path)
    code, output = check.run(["-m", "nagini_translation.main", str(path)], "extra_change")
    assert code == 1, output
    assert "Verification failed" in output, output
    assert (
        "Assertion Forall(int, lambda i: Implies(1 <= i and i < len(values), "
        "values[i] == before[i])) might not hold."
    ) in output, output
