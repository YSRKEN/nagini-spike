"""進捗表と台帳の一致、更新漏れの拒否を検査する。"""

from pathlib import Path

import pytest

from scripts.render_progress import render, synchronize


@pytest.mark.parametrize(
    ("status", "label"),
    (
        ("verified", "done（証明成功）"),
        ("unconfirmed", "未確認"),
        ("unsupported", "done（非対応確認）"),
        ("translation_failed", "done（変換失敗確認）"),
        ("rejected_incorrect", "done（誤実装拒否）"),
        ("insufficient_specification", "done（仕様不足確認）"),
    ),
)
def test_all_states(status: str, label: str) -> None:
    """調査済みと証明成功を取り違えず、全状態を表示する。"""
    text = render([{"id": "sample", "question": "問い", "status": status, "evidence": []}])
    assert label in text
    assert "sample" in text
    assert "問い" in text


def test_preserves_rows_and_escapes_cells() -> None:
    """未確認行を消さず、表を壊す区切りや改行を整える。"""
    text = render([
        {"id": "one", "question": "A|B\nC", "status": "verified", "evidence": ["examples/a.py"]},
        {"id": "two", "question": "未調査", "status": "unconfirmed", "evidence": []},
    ])
    assert "全2件" in text
    assert "調査済み1件" in text
    assert "未確認1件" in text
    assert "A\\|B C" in text
    assert "../examples/a.py" in text
    assert "two" in text


def test_stale_table_is_rejected_then_regenerated(tmp_path: Path) -> None:
    """更新忘れを検出し、生成後だけ検査に通す。"""
    target = tmp_path / "progress.md"
    assert synchronize(target, "新しい表\n", check=True) == 1
    assert not target.exists()
    assert synchronize(target, "新しい表\n", check=False) == 0
    assert synchronize(target, "新しい表\n", check=True) == 0
    assert synchronize(target, "変更した表\n", check=True) == 1
    assert target.read_text(encoding="utf-8") == "新しい表\n"
