"""完了候補の明示がなければ完了検査本体の呼び出しを止める。"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

import scripts.check_investigation as investigation


@pytest.mark.parametrize(
    "arguments,expected,required",
    [
        ([], 0, False),
        (["--require-complete"], 2, None),
        (["--candidate-reviewed"], 2, None),
        (["--require-complete", "--candidate-reviewed"], 0, True),
    ],
)
def test_completion_entry(
    arguments: list[str],
    expected: int,
    required: bool | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """合成検査で、実台帳を読まずに入口の条件と呼び出し有無を照合する。"""
    calls: list[bool] = []

    def probe(path: Path, root: Path, *, require_complete: bool = False) -> list[str]:
        """検査本体への到達を記録する。"""
        calls.append(require_complete)
        return []

    monkeypatch.setattr(investigation, "validate", probe)
    monkeypatch.setattr(sys, "argv", ["check_investigation.py", *arguments])
    assert investigation.main() == expected
    assert calls == ([] if required is None else [required])


def test_optimized_entry_stops_before_ledger_read(tmp_path: Path) -> None:
    """最適化モードでも、未レビューの要求は存在しない合成台帳を読む前に止まる。"""
    script = Path(investigation.__file__).resolve()
    process = subprocess.run(
        [
            sys.executable,
            "-O",
            str(script),
            "--require-complete",
            "--ledger",
            str(tmp_path / "missing.json"),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    assert process.returncode == 2
    assert "完了候補" in process.stdout
    assert "台帳を読み取れません" not in process.stdout
